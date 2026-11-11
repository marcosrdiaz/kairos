"""Avisos por noticia (`kind=news_estimate`, T4-31).

Una noticia avisa si el extremo de su rango más cercano a cero supera el umbral de la cartera
(D-032) multiplicado por el factor de su perfil: conservador 0,6, moderado 1, agresivo 1,5.
Comparte el límite semanal por cartera con `event_impact` y `market_move`; como mucho un aviso
nuevo por cartera y día; el medido rehace el aviso del estimado en lugar de crear otro.

Las noticias son falsas (`_FakeNews` sustituye a `news_service.list_for_portfolio`), pero sus
cifras están trazadas: aquí se prueba la regla de aviso, no la estimación (T4-30).
"""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.agents import claude, guardian
from app.alerts import config, engine, news_estimate, repository
from app.alerts import service as alerts_service
from app.core import clock, trace
from app.events import service as events_service
from app.main import API_PREFIX
from app.news import service as news_service
from app.portfolio import service as portfolio_service
from app.schemas.alerts import AlertKind
from app.schemas.common import Confidence, Polarity, SourceKind, SourceRef
from app.schemas.events import Relevance
from app.schemas.news import (
    NewsCategory,
    NewsEstimateMethod,
    NewsEstimateOut,
    NewsEstimateStatus,
    NewsItemOut,
)

NOW = datetime(2026, 11, 6, 18, 0, tzinfo=UTC)  # viernes, último cierre de `data/prices`
CSV = "asset;units;avg_cost_eur\nNVDA;40;100\n"
BIG_EVENT = "nvda-2025-02"
TOTAL = Decimal("42000")  # umbral base = max(150, 0,005 · 42.000) = 210 €


def _d(value: str) -> Decimal:
    return Decimal(value)


# --- Regla (pura) ---


@pytest.mark.parametrize(
    ("low", "high", "expected"),
    [("-500", "-300", "-300"), ("200", "400", "200"), ("-100", "300", "0"), ("0", "50", "0")],
)
def test_closest_to_zero(low: str, high: str, expected: str) -> None:
    assert news_estimate.closest_to_zero(_d(low), _d(high)) == _d(expected)


@pytest.mark.parametrize(
    ("risk_profile", "legacy", "factor"),
    [
        ("conservador", None, "0.6"),
        ("moderado", None, "1.0"),
        ("agresivo", None, "1.5"),
        (None, "dinamico", "1.5"),  # `Profile` obsoleto de Laura
        (None, "conservador", "0.6"),
        (None, None, "1"),  # sin perfil: el de moderado
    ],
)
def test_profile_factor(risk_profile: str | None, legacy: str | None, factor: str) -> None:
    assert news_estimate.profile_factor(risk_profile, legacy) == _d(factor)


def test_score_uses_the_end_closest_to_zero_and_the_profile() -> None:
    # Extremo cercano 252 € frente a 210 € × factor.
    assert news_estimate.score_if_alert(_d("-400"), _d("-252"), TOTAL, _d("1")) == _d("1.2")
    assert news_estimate.score_if_alert(_d("-400"), _d("-252"), TOTAL, _d("1.5")) is None
    assert news_estimate.score_if_alert(_d("-400"), _d("-252"), TOTAL, _d("0.6")) == _d("2")


def test_a_range_that_crosses_zero_never_alerts() -> None:
    assert news_estimate.score_if_alert(_d("-5000"), _d("10"), TOTAL, _d("0.6")) is None


# --- Servicio ---


@pytest.fixture(autouse=True)
def _setup(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    clock.set_now(NOW)
    claude.set_client(None)
    alerts_service.reset_news_checks()
    monkeypatch.setattr(config, "NEWS_ESTIMATE_IN_DEMO", True)
    yield
    alerts_service.reset_news_checks()


def _item(
    news_id: str,
    low: Decimal,
    high: Decimal,
    *,
    status: NewsEstimateStatus = NewsEstimateStatus.ESTIMATED,
    published: datetime = NOW - timedelta(hours=2),
    event_id: str | None = None,
) -> NewsItemOut:
    calc_id = trace.record(
        "scenario", "noticia de prueba", {"news_id": news_id}, {"low": low, "high": high}, []
    )
    impact = (low + high) / 2
    measured = status is NewsEstimateStatus.MEASURED
    return NewsItemOut(
        id=news_id,
        category=NewsCategory.EARNINGS,
        title="Nvidia presenta resultados trimestrales",
        summary="Resumen.",
        published_at=published,
        source=SourceRef(kind=SourceKind.EVENT, label="Prueba", ref=news_id, as_of=published),
        companies=[],
        asset_ids=["NVDA"],
        channels=[],
        causal_chain=[],
        relevance=Relevance.HIGH,
        estimate=NewsEstimateOut(
            status=status,
            polarity=Polarity.RIESGO if impact < 0 else Polarity.OPORTUNIDAD,
            impact_eur=impact,
            low_eur=low,
            high_eur=high,
            impact_pct=_d("-0.01"),
            low_pct=_d("-0.02"),
            high_pct=_d("-0.005"),
            horizon_sessions=1 if measured else 5,
            confidence=Confidence.MEDIA,
            method=NewsEstimateMethod.MEASURED if measured else NewsEstimateMethod.VOLATILITY,
            analogs_count=None if measured else 25,
            calc_id=calc_id,
            event_id=event_id,
            as_of=NOW,
        ),
    )


class _FakeNews:
    """Las mismas noticias para todas las carteras."""

    def __init__(self, *items: NewsItemOut) -> None:
        self.items = list(items)
        self.calls: list[str] = []

    def __call__(
        self, portfolio_id: str, category: Any = None, affecting: bool = True, limit: int = 50
    ) -> list[NewsItemOut]:
        self.calls.append(portfolio_id)
        return self.items


def _base(portfolio_id: str) -> Decimal:
    return engine.threshold_eur(portfolio_service.get_valued(portfolio_id).total_eur)


def _falling(portfolio_id: str, times: str) -> tuple[Decimal, Decimal]:
    """Rango a la baja cuyo extremo cercano a cero es `times` veces el umbral base."""
    near = (_base(portfolio_id) * _d(times)).quantize(_d("0.01"))
    return -near * 2, -near


def _news_alerts(client: TestClient, portfolio_id: str = "laura") -> list[dict[str, Any]]:
    response = client.get(f"{API_PREFIX}/portfolios/{portfolio_id}/alerts")
    assert response.status_code == 200, response.text
    return [a for a in response.json() if a["kind"] == "news_estimate"]


def _import(client: TestClient, name: str, risk_profile: str) -> str:
    body = {"name": name, "kind": "personal", "risk_profile": risk_profile, "csv": CSV}
    response = client.post(f"{API_PREFIX}/portfolios/import", json=body)
    assert response.status_code == 201, response.text
    portfolio_id: str = response.json()["portfolio"]["id"]
    return portfolio_id


@pytest.mark.parametrize(
    ("risk_profile", "times", "alerts"),
    [
        ("conservador", "0.8", True),  # 0,8 ≥ 0,6
        ("conservador", "0.5", False),
        ("moderado", "1.2", True),
        ("moderado", "0.8", False),
        ("agresivo", "1.6", True),
        ("agresivo", "1.2", False),  # 1,2 < 1,5
    ],
)
def test_each_profile_has_its_threshold(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    risk_profile: str,
    times: str,
    alerts: bool,
) -> None:
    portfolio_id = _import(client, "Prueba", risk_profile)
    monkeypatch.setattr(
        news_service, "list_for_portfolio", _FakeNews(_item("n1", *_falling(portfolio_id, times)))
    )
    assert len(_news_alerts(client, portfolio_id)) == (1 if alerts else 0)


def test_same_news_alerts_the_conservative_portfolio_and_not_the_aggressive(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    ids = {p: _import(client, p, p) for p in ("conservador", "moderado", "agresivo")}
    news = _item("n1", *_falling(ids["moderado"], "0.9"))  # mismas posiciones, mismo umbral base
    monkeypatch.setattr(news_service, "list_for_portfolio", _FakeNews(news))

    got = {p: len(_news_alerts(client, pid)) for p, pid in ids.items()}

    assert got == {"conservador": 1, "moderado": 0, "agresivo": 0}


def test_alert_carries_news_id_calc_id_range_and_horizon(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    news = _item("n1", _d("-2400"), _d("-1200"))
    monkeypatch.setattr(news_service, "list_for_portfolio", _FakeNews(news))

    (alert,) = _news_alerts(client)

    assert alert["news_id"] == "n1"
    assert alert["event_id"] is None
    assert news.estimate is not None and alert["calc_id"] == news.estimate.calc_id
    assert trace.get(alert["calc_id"]) is not None  # cifra trazable (regla 4)
    message = alert["message"]
    assert "se estima" in message
    assert "entre 1.200 euros y 2.400 euros" in message
    assert "próximas 5 sesiones" in message
    assert guardian.find_forbidden(message) == []


def test_ranges_crossing_zero_and_old_news_do_not_alert(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    crossing = _item("n1", _d("-5000"), _d("100"))
    old = _item("n2", _d("-5000"), _d("-4000"), published=NOW - config.NEWS_LOOKBACK * 2)
    monkeypatch.setattr(news_service, "list_for_portfolio", _FakeNews(crossing, old))
    assert _news_alerts(client) == []


def test_one_new_news_alert_per_day_the_biggest_first(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    small = _item("n1", _d("-2000"), _d("-1000"))
    big = _item("n2", _d("-6000"), _d("-3000"))
    monkeypatch.setattr(news_service, "list_for_portfolio", _FakeNews(small, big))

    assert [a["news_id"] for a in _news_alerts(client)] == ["n2"]
    alerts_service.reset_news_checks()
    assert len(_news_alerts(client)) == 1  # el mismo día, no

    clock.set_now(NOW + timedelta(days=1))
    alerts_service.reset_news_checks()
    assert sorted(a["news_id"] for a in _news_alerts(client)) == ["n1", "n2"]


def test_full_week_blocks_news_alerts(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    for _ in range(config.WEEKLY_LIMIT):
        repository.save("laura", None, AlertKind.MARKET_MOVE, _d("1"), "Relleno.", clock.now())
    monkeypatch.setattr(
        news_service, "list_for_portfolio", _FakeNews(_item("n1", _d("-3000"), _d("-2000")))
    )
    assert _news_alerts(client) == []


def test_measured_updates_the_estimated_alert_instead_of_adding_one(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        news_service, "list_for_portfolio", _FakeNews(_item("n1", _d("-3000"), _d("-2000")))
    )
    (estimated,) = _news_alerts(client)

    measured = _item("n1", _d("-1900"), _d("-1700"), status=NewsEstimateStatus.MEASURED)
    monkeypatch.setattr(news_service, "list_for_portfolio", _FakeNews(measured))
    alerts_service.reset_news_checks()
    (alert,) = _news_alerts(client)

    assert alert["id"] == estimated["id"]
    assert alert["created_at"] == estimated["created_at"]
    assert measured.estimate is not None and alert["calc_id"] == measured.estimate.calc_id
    assert "ya medido" in alert["message"] and "1.800 euros" in alert["message"]
    assert "entre 1.700 euros y 1.900 euros" in alert["message"]
    assert guardian.find_forbidden(alert["message"]) == []
    start, end = engine.iso_week_bounds(NOW)
    assert repository.count_between("laura", start, end) == 1  # no gasta cupo


def test_no_double_alert_when_the_measured_event_already_alerted(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    events_service.replay(BIG_EVENT)  # aviso `event_impact` para Laura
    assert repository.exists("laura", BIG_EVENT, AlertKind.EVENT_IMPACT)
    measured = _item(
        "n1", _d("-3000"), _d("-2000"), status=NewsEstimateStatus.MEASURED, event_id=BIG_EVENT
    )
    monkeypatch.setattr(news_service, "list_for_portfolio", _FakeNews(measured))
    assert _news_alerts(client) == []


def test_off_in_demo_mode_by_default_but_can_be_forced(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(config, "NEWS_ESTIMATE_IN_DEMO", False)
    fake = _FakeNews(_item("n1", _d("-3000"), _d("-2000")))
    monkeypatch.setattr(news_service, "list_for_portfolio", fake)

    assert _news_alerts(client) == []
    assert fake.calls == []

    assert alerts_service.check_news("laura", force=True) == 1  # `make news-alerts`
    assert alerts_service.check_news("laura", force=True) == 0  # repetirlo no duplica
    assert len(_news_alerts(client)) == 1


def test_polling_does_not_recompute_the_news_every_time(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = _FakeNews()
    monkeypatch.setattr(news_service, "list_for_portfolio", fake)
    for _ in range(3):
        _news_alerts(client)
    assert fake.calls == ["laura"]
    clock.set_now(NOW + config.NEWS_CHECK_EVERY)
    _news_alerts(client)
    assert fake.calls == ["laura", "laura"]
