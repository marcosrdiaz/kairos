"""Avisos de evento: umbral, idempotencia, límite semanal, guardián y cascada (T2-08, D-032)."""

import json
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event as sa_event
from sqlalchemy import inspect, text

from app.agents import claude
from app.alerts import engine, repository
from app.alerts import service as alerts_service
from app.core import clock
from app.core.db import get_engine, session_scope
from app.events import service as events_service
from app.main import API_PREFIX
from app.schemas.alerts import AlertKind
from app.schemas.events import ReplayRequest
from tests.fakes.claude_stream import FakeStreamingClaude, Reply

NOW = datetime(2026, 11, 8, 18, 0, tzinfo=UTC)  # domingo: semana ISO del 2 al 8
BIG = "nvda-2025-02"  # Laura: -224,86 € sobre ~42.364 € (umbral ~211,8 €). Javier: no llega.
SMALL = ("bce-2025-06", "oil-2025-06")  # Laura: menos de 25 € en los dos


@pytest.fixture(autouse=True)
def _clean() -> Iterator[None]:
    clock.set_now(NOW)
    yield
    claude.set_client(None)


def _alerts(client: TestClient, portfolio_id: str = "laura") -> list[dict[str, Any]]:
    response = client.get(f"{API_PREFIX}/portfolios/{portfolio_id}/alerts")
    assert response.status_code == 200
    body: list[dict[str, Any]] = response.json()
    return body


def _filler(portfolio_id: str, kind: AlertKind = AlertKind.EVENT_IMPACT) -> None:
    repository.save(
        portfolio_id,
        None,
        kind,
        engine.score(Decimal("1"), Decimal("1")),
        "Aviso de relleno.",
        clock.now(),
    )


def test_big_event_alerts_only_the_portfolio_it_moves(client: TestClient) -> None:
    events_service.replay(BIG)
    laura, javier = _alerts(client, "laura"), _alerts(client, "javier")
    assert [a["event_id"] for a in laura] == [BIG]
    assert laura[0]["kind"] == "event_impact"
    assert laura[0]["delivered"] is False
    assert laura[0]["created_at"] == "2026-11-08T18:00:00Z"
    assert javier == []


def test_alert_points_to_the_impact_trace_and_scores_at_least_one(client: TestClient) -> None:
    events_service.replay(BIG)
    alert = _alerts(client)[0]
    impact = client.get(f"{API_PREFIX}/portfolios/laura/events").json()[0]
    assert alert["calc_id"] == impact["calc_id"]
    assert client.get(f"{API_PREFIX}/traces/{alert['calc_id']}").status_code == 200
    assert float(alert["score"]) >= 1


def test_small_events_do_not_alert(client: TestClient) -> None:
    for event_id in SMALL:
        events_service.replay(event_id)
    assert _alerts(client) == []


def test_alert_and_widget_turn_on_together(client: TestClient) -> None:
    """Paso 3 del guion: el aviso y el estado «Atento» salen del mismo evento."""
    events_service.replay(BIG)
    status = client.get(f"{API_PREFIX}/portfolios/laura/status").json()
    assert status["state"] == "atento"
    assert status["reason"]["event_id"] == _alerts(client)[0]["event_id"]
    events_service.replay("oil-2025-06")
    assert [a["event_id"] for a in _alerts(client)] == [BIG]


def test_silent_replay_does_not_alert(client: TestClient) -> None:
    events_service.replay(BIG, ReplayRequest(silent=True))
    assert _alerts(client) == []


def test_replaying_twice_creates_one_alert_and_spends_one_slot(client: TestClient) -> None:
    events_service.replay(BIG)
    events_service.replay(BIG)
    assert len(_alerts(client)) == 1
    start, end = engine.iso_week_bounds(clock.now())
    assert repository.count_between("laura", start, end) == 1


def test_idempotency_survives_a_new_week(client: TestClient) -> None:
    events_service.replay(BIG)
    clock.set_now(NOW + timedelta(days=8))
    events_service.replay(BIG)
    assert len(_alerts(client)) == 1


def test_weekly_limit_blocks_a_third_alert(client: TestClient) -> None:
    _filler("laura")
    _filler("laura")
    events_service.replay(BIG)
    assert [a["message"] for a in _alerts(client)] == ["Aviso de relleno."] * 2


def test_limit_resets_on_monday(client: TestClient) -> None:
    _filler("laura")
    _filler("laura")
    clock.set_now(datetime(2026, 11, 9, 0, 0, tzinfo=UTC))  # lunes: semana ISO nueva
    events_service.replay(BIG)
    assert BIG in [a["event_id"] for a in _alerts(client)]


def test_limit_is_per_portfolio(client: TestClient) -> None:
    _filler("javier")
    _filler("javier")
    events_service.replay(BIG)
    assert [a["event_id"] for a in _alerts(client, "laura")] == [BIG]


def test_dca_pending_does_not_use_the_weekly_slots(client: TestClient) -> None:
    _filler("laura", AlertKind.DCA_PENDING)
    _filler("laura", AlertKind.DCA_PENDING)
    _filler("laura", AlertKind.DCA_PENDING)
    events_service.replay(BIG)
    assert BIG in [a["event_id"] for a in _alerts(client)]


def test_alerts_of_an_unknown_portfolio_are_not_found(client: TestClient) -> None:
    assert client.get(f"{API_PREFIX}/portfolios/nadie/alerts").status_code == 404


def test_alerts_are_listed_newest_first(client: TestClient) -> None:
    _filler("laura")
    clock.set_now(NOW + timedelta(hours=1))
    events_service.replay(BIG)
    assert [a["event_id"] for a in _alerts(client)] == [BIG, None]


# --- Mensaje: cifra real y guardián ---


class _AlertClaude:
    """Para el aviso responde `alert_text(display)`; el resto de textos, sin cifras."""

    def __init__(self, alert_text: str) -> None:
        self.alert_text = alert_text
        self.alert_calls = 0
        self.messages = self

    def stream(self, **kwargs: Any) -> Any:
        content = kwargs["messages"][0]["content"]
        if "aviso al móvil" not in content:
            return FakeStreamingClaude(Reply("Tu cartera sigue igual.")).messages.stream(**kwargs)
        self.alert_calls += 1
        facts = json.loads(content.split("<facts>\n")[1].split("\n</facts>")[0])
        display = next(f["display"] for f in facts if f["key"] == "impact")
        reply = Reply(self.alert_text.format(display=display))
        return FakeStreamingClaude(reply).messages.stream(**kwargs)


def test_message_from_the_model_uses_the_real_impact_figure(client: TestClient) -> None:
    claude.set_client(_AlertClaude("Tu cartera pierde unos {display} por este evento."))
    events_service.replay(BIG)
    impact = client.get(f"{API_PREFIX}/portfolios/laura/events").json()[0]
    message = _alerts(client)[0]["message"]
    assert message.startswith("Tu cartera pierde unos ")
    assert "225" in message
    assert impact["impact_eur"] == "-224.86"


def test_blocked_message_falls_back_to_the_template_with_the_real_figure(
    client: TestClient,
) -> None:
    fake = _AlertClaude("Tu cartera pierde unos 600 euros por este evento.")
    claude.set_client(fake)
    events_service.replay(BIG)
    message = _alerts(client)[0]["message"]
    assert fake.alert_calls >= 1
    assert "600" not in message
    assert "unos 225 euros menos" in message


def test_order_in_the_message_is_blocked(client: TestClient) -> None:
    claude.set_client(_AlertClaude("Te recomiendo vender: pierdes unos {display}."))
    events_service.replay(BIG)
    message = _alerts(client)[0]["message"]
    assert "recomiendo" not in message
    assert "vender" not in message
    assert "unos 225 euros menos" in message


# --- Cascada al borrar eventos (/demo/reset) ---


@pytest.fixture
def foreign_keys_on() -> Iterator[None]:
    """SQLite ignora las claves foráneas salvo con el PRAGMA; Postgres siempre las aplica."""

    @sa_event.listens_for(get_engine(), "connect")
    def _enable(dbapi_connection: Any, _: Any) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    get_engine().dispose()  # las conexiones nuevas ya llevan el PRAGMA
    yield


def test_deleting_events_deletes_their_alerts(client: TestClient, foreign_keys_on: None) -> None:
    events_service.replay(BIG)
    assert len(_alerts(client)) == 1
    from app.impact import service as impact_service

    impact_service.reset()
    events_service.reset()
    with session_scope() as session:
        assert session.execute(text("SELECT COUNT(*) FROM alert")).scalar() == 0
    assert _alerts(client) == []


def test_alert_foreign_keys_cascade_in_the_schema(client: TestClient) -> None:
    """Lo que hace cumplir Postgres: `ON DELETE CASCADE` en el DDL, no solo en el modelo."""
    options = {
        fk["constrained_columns"][0]: fk["options"].get("ondelete")
        for fk in inspect(get_engine()).get_foreign_keys("alert")
    }
    assert options == {"portfolio_id": "CASCADE", "event_id": "CASCADE"}


def test_evaluate_without_impact_does_nothing(client: TestClient) -> None:
    alerts_service.evaluate("laura", "oil-2025-06")
    assert _alerts(client) == []
