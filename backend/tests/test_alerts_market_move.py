"""Aviso por movimiento de mercado (`kind=market_move`, T2-21; D-032).

Salta si la cartera varía en un día por encima del umbral de aviso y la parte sin evento que la
explique también lo supera. Comparte puntuación, umbral y límite semanal con `event_impact`.
"""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.agents import claude, guardian
from app.alerts import config, engine, market_move, repository
from app.alerts import service as alerts_service
from app.core import clock, trace
from app.events import service as events_service
from app.impact import service as impact_service
from app.main import API_PREFIX
from app.schemas.alerts import AlertKind
from app.schemas.impact import MoveAttributionOut, MoveEventImpact, MovePeriod

NOW = datetime(2026, 11, 6, 18, 0, tzinfo=UTC)  # viernes, último cierre de `data/prices`
TOTAL = Decimal("42000")  # umbral = max(150, 0,005 · 42.000) = 210 €
BIG_EVENT = "nvda-2025-02"  # Laura: aviso `event_impact` (ver `test_alerts_service.py`)


def _d(value: str) -> Decimal:
    return Decimal(value)


# --- Regla (pura) ---


@pytest.mark.parametrize(
    ("change", "unexplained", "expected"),
    [
        ("-100", "-100", None),  # la cartera apenas se mueve
        ("-600", "-50", None),  # se mueve, pero un evento lo explica casi todo
        ("-600", "-420", Decimal("2")),  # se mueve y casi nada lo explica: score de lo no explicado
        ("315", "315", Decimal("1.5")),  # también al alza
        ("-210", "-210", Decimal("1")),  # justo en el umbral, como `event_impact`
        ("-50", "-400", None),  # lo no explicado es grande, pero la cartera apenas varía
    ],
)
def test_score_needs_a_big_move_that_events_do_not_explain(
    change: str, unexplained: str, expected: Decimal | None
) -> None:
    assert market_move.score_if_alert(_d(change), _d(unexplained), TOTAL) == expected


def test_score_uses_the_same_threshold_as_event_alerts() -> None:
    score = market_move.score_if_alert(_d("-500"), _d("-500"), TOTAL)
    assert score == engine.score(_d("-500"), TOTAL)


def test_day_bounds_are_the_utc_calendar_day() -> None:
    late = datetime(2026, 11, 6, 23, 30, tzinfo=UTC)
    start, end = market_move.day_bounds(late)
    assert start == datetime(2026, 11, 6, tzinfo=UTC)
    assert end == start + timedelta(days=1)


# --- Servicio ---


@pytest.fixture(autouse=True)
def _setup(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    clock.set_now(NOW)
    claude.set_client(None)  # sin modelo: la frase sale de plantilla (validada por el guardián)
    alerts_service.reset_market_move_checks()
    monkeypatch.setattr(config, "MARKET_MOVE_IN_DEMO", True)
    yield
    alerts_service.reset_market_move_checks()


class _FakeMove:
    """Sustituye a `impact_service.explain_move` con un movimiento del día fijo y trazado."""

    def __init__(
        self, change: str, unexplained: str, by_event: list[MoveEventImpact] | None = None
    ) -> None:
        self.change, self.unexplained, self.by_event = change, unexplained, by_event or []
        self.calls: list[str] = []

    def __call__(self, portfolio_id: str, period: MovePeriod) -> MoveAttributionOut:
        assert period == "day"
        self.calls.append(portfolio_id)
        calc_id = trace.record(
            "move",
            "movimiento de prueba",
            {"portfolio_id": portfolio_id, "period": period},
            {"change_eur": self.change},
            [],
        )
        return MoveAttributionOut(
            period=period,
            start=NOW - timedelta(days=1),
            end=NOW,
            change_eur=_d(self.change),
            change_pct=Decimal("-0.01"),
            by_asset=[],
            by_event=self.by_event,
            unexplained_eur=_d(self.unexplained),
            calc_id=calc_id,
        )


def _alerts(client: TestClient, portfolio_id: str = "laura") -> list[dict[str, Any]]:
    response = client.get(f"{API_PREFIX}/portfolios/{portfolio_id}/alerts")
    assert response.status_code == 200, response.text
    body: list[dict[str, Any]] = response.json()
    return body


def _market(alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [a for a in alerts if a["kind"] == "market_move"]


def test_unexplained_big_move_alerts_with_its_calc_id(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = _FakeMove("-900", "-900")
    monkeypatch.setattr(impact_service, "explain_move", fake)

    alerts = _market(_alerts(client))

    assert len(alerts) == 1
    alert = alerts[0]
    assert alert["event_id"] is None
    assert alert["calc_id"] is not None
    assert trace.get(alert["calc_id"]) is not None  # cifra trazable (regla 4)
    assert Decimal(alert["score"]) >= 1
    assert "900 euros" in alert["message"]
    assert guardian.find_forbidden(alert["message"]) == []


def test_explained_or_small_moves_do_not_alert(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    explained = MoveEventImpact(
        event_id=BIG_EVENT,
        title="Resultados",
        impact_eur=_d("-880"),
        low_eur=_d("-950"),
        high_eur=_d("-800"),
    )
    monkeypatch.setattr(impact_service, "explain_move", _FakeMove("-900", "-20", [explained]))
    assert _market(_alerts(client)) == []

    alerts_service.reset_market_move_checks()
    monkeypatch.setattr(impact_service, "explain_move", _FakeMove("-80", "-80"))
    assert _market(_alerts(client)) == []


def test_one_market_alert_per_portfolio_and_day(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(impact_service, "explain_move", _FakeMove("-900", "-900"))
    _alerts(client)
    alerts_service.reset_market_move_checks()  # aunque se vuelva a comprobar el mismo día
    assert len(_market(_alerts(client))) == 1

    clock.set_now(NOW + timedelta(days=1))  # al día siguiente sí puede volver a avisar
    alerts_service.reset_market_move_checks()
    assert len(_market(_alerts(client))) == 2


def test_polling_does_not_recompute_the_move_every_time(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = _FakeMove("-80", "-80")
    monkeypatch.setattr(impact_service, "explain_move", fake)
    for _ in range(3):
        _alerts(client)
    assert fake.calls == ["laura"]
    clock.set_now(NOW + config.MARKET_MOVE_CHECK_EVERY)
    _alerts(client)
    assert fake.calls == ["laura", "laura"]


def test_disabled_in_demo_mode_by_default(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(config, "MARKET_MOVE_IN_DEMO", False)
    fake = _FakeMove("-900", "-900")
    monkeypatch.setattr(impact_service, "explain_move", fake)
    assert _market(_alerts(client)) == []
    assert fake.calls == []


def _filler(kind: AlertKind) -> None:
    repository.save("laura", None, kind, Decimal("1"), "Aviso de relleno.", clock.now())


def test_full_week_blocks_market_alerts(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _filler(AlertKind.EVENT_IMPACT)
    _filler(AlertKind.EVENT_IMPACT)
    monkeypatch.setattr(impact_service, "explain_move", _FakeMove("-900", "-900"))
    assert _market(_alerts(client)) == []


def test_market_alerts_use_the_shared_weekly_slots(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(impact_service, "explain_move", _FakeMove("-900", "-900"))
    assert len(_market(_alerts(client))) == 1
    _filler(AlertKind.EVENT_IMPACT)  # 2 de 2 en la semana ISO

    events_service.replay(BIG_EVENT)  # superaría el umbral, pero ya no queda cupo
    alerts = _alerts(client)
    assert sorted(a["kind"] for a in alerts) == ["event_impact", "market_move"]
    assert all(a["event_id"] is None for a in alerts)  # el del evento no ha entrado


def test_real_move_runs_end_to_end(client: TestClient) -> None:
    """Con `explain_move` real: o no hay aviso, o lo hay con traza y por encima del umbral."""
    for alert in _market(_alerts(client)):
        assert alert["calc_id"] is not None
        assert trace.get(alert["calc_id"]) is not None
        assert Decimal(alert["score"]) >= 1
