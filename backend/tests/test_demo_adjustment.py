"""Ajuste de demo tras un replay (T2-02, D-031): la valoración suma el impacto de cada posición."""

from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.core import clock
from app.events import service as events_service
from app.main import API_PREFIX
from app.portfolio import engine
from app.portfolio import service as portfolio_service
from app.schemas.common import AssetClass, AssetType, PriceKind
from app.schemas.impact import EventImpactOut

NOW = datetime(2026, 11, 8, 18, 0, tzinfo=UTC)
EVENT = "nvda-2025-02"
LABEL = "Estimación tras el evento"


@pytest.fixture(autouse=True)
def _fixed_clock() -> Iterator[None]:
    clock.set_now(NOW)
    yield


def _portfolio(client: TestClient, portfolio_id: str = "laura") -> dict[str, Any]:
    response = client.get(f"{API_PREFIX}/portfolios/{portfolio_id}")
    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    return body


def _event_impact(client: TestClient, event_id: str, portfolio_id: str = "laura") -> dict[str, Any]:
    events = client.get(f"{API_PREFIX}/portfolios/{portfolio_id}/events").json()
    return next(e for e in events if e["event_id"] == event_id)


def _replay(client: TestClient, event_id: str = EVENT) -> None:
    assert client.post(f"{API_PREFIX}/demo/replay/{event_id}").status_code == 200


# --- Motor (puro) ---


def _asset(asset_id: str, asset_class: AssetClass) -> engine.AssetIn:
    return engine.AssetIn(asset_id, None, None, asset_id, AssetType.ETF, asset_class, False)


def _quote(price: str, week_ago: str | None) -> engine.QuoteIn:
    return engine.QuoteIn(
        price=Decimal(price),
        currency="EUR",
        price_at=NOW,
        price_kind=PriceKind.INTRADAY,
        fx_rate=Decimal(1),
        week_ago_unit_eur=Decimal(week_ago) if week_ago is not None else None,
    )


def _lot(asset_id: str, units: str, cost: str) -> engine.LotIn:
    return engine.LotIn(asset_id, NOW, Decimal(units), Decimal(cost))


ASSETS = {"A": _asset("A", AssetClass.EQUITY), "B": _asset("B", AssetClass.FIXED_INCOME)}
LOTS = [_lot("A", "10", "8"), _lot("B", "10", "10")]


def test_engine_adds_the_adjustment_to_value_total_and_week_change() -> None:
    quotes = {"A": _quote("10", "10"), "B": _quote("10", "10")}
    out = engine.value_portfolio(LOTS, ASSETS, quotes, adjustments={"A": Decimal("-5.00")})
    a = next(p for p in out.positions if p.asset_id == "A")
    assert a.value_eur == Decimal("95.00")
    assert a.unrealized_pnl_eur == Decimal("15.00")
    assert out.total_eur == Decimal("195.00")
    assert out.change_week_eur == Decimal("-5.00")
    assert out.change_week_pct == Decimal("-0.0250")
    assert out.allocation.equity == Decimal("0.4872")


def test_engine_keeps_the_adjustment_in_the_week_change_without_week_data() -> None:
    quotes = {"A": _quote("10", None), "B": _quote("10", "10")}
    out = engine.value_portfolio(LOTS, ASSETS, quotes, adjustments={"A": Decimal("-5.00")})
    assert out.change_week_eur == Decimal("-5.00")


def test_engine_ignores_adjustments_of_assets_not_held() -> None:
    quotes = {"A": _quote("10", "10"), "B": _quote("10", "10")}
    out = engine.value_portfolio(LOTS, ASSETS, quotes, adjustments={"Z": Decimal("-5.00")})
    assert out.total_eur == Decimal("200.00")


# --- Servicio y API ---


def test_without_replay_there_are_no_adjustments(client: TestClient) -> None:
    assert _portfolio(client)["demo_adjustments"] == []


def test_replay_moves_the_valuation_by_the_event_impact(client: TestClient) -> None:
    before = _portfolio(client)
    _replay(client)
    after = _portfolio(client)
    impact = _event_impact(client, EVENT)

    assert after["demo_adjustments"] == [
        {
            "event_id": EVENT,
            "impact_eur": impact["impact_eur"],
            "label": LABEL,
            "calc_id": impact["calc_id"],
        }
    ]
    delta = Decimal(after["total_eur"]) - Decimal(before["total_eur"])
    assert delta == Decimal(impact["impact_eur"])
    week_delta = Decimal(after["change_week_eur"]) - Decimal(before["change_week_eur"])
    assert week_delta == Decimal(impact["impact_eur"])

    values_before = {p["asset_id"]: Decimal(p["value_eur"]) for p in before["positions"]}
    for row in impact["breakdown"]:
        position = next(p for p in after["positions"] if p["asset_id"] == row["asset_id"])
        expected = values_before[row["asset_id"]] + Decimal(row["impact_eur"])
        assert Decimal(position["value_eur"]) == expected
    assert sum(Decimal(p["value_eur"]) for p in after["positions"]) == Decimal(after["total_eur"])


def test_status_reflects_the_adjusted_valuation(client: TestClient) -> None:
    _replay(client)
    status = client.get(f"{API_PREFIX}/portfolios/laura/status").json()
    assert status["total_eur"] == _portfolio(client)["total_eur"]


def test_valuation_trace_points_to_the_event_impact(client: TestClient) -> None:
    _replay(client)
    body = _portfolio(client)
    trace = client.get(f"{API_PREFIX}/traces/{body['calc_id']}").json()
    assert body["demo_adjustments"][0]["calc_id"] in trace["parent_calc_ids"]
    assert trace["inputs"]["demo_adjustments"]


def test_replaying_the_same_event_does_not_stack(client: TestClient) -> None:
    _replay(client)
    first = _portfolio(client)
    _replay(client)
    second = _portfolio(client)
    assert second["total_eur"] == first["total_eur"]
    assert len(second["demo_adjustments"]) == 1


def test_two_events_add_up(client: TestClient) -> None:
    before = _portfolio(client)
    _replay(client, "bce-2025-06")
    _replay(client, EVENT)
    after = _portfolio(client)
    assert [a["event_id"] for a in after["demo_adjustments"]] == ["bce-2025-06", EVENT]
    total = sum(Decimal(a["impact_eur"]) for a in after["demo_adjustments"])
    assert Decimal(after["total_eur"]) - Decimal(before["total_eur"]) == total


def test_demo_reset_clears_the_adjustments(client: TestClient) -> None:
    before = _portfolio(client)
    _replay(client)
    assert client.post(f"{API_PREFIX}/demo/reset").status_code == 200
    after = _portfolio(client)
    assert after["demo_adjustments"] == []
    assert after["total_eur"] == before["total_eur"]


def test_apply_does_nothing_outside_demo_mode(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    events_service.replay(EVENT)
    impact = _event_impact(client, EVENT)
    portfolio_service.clear_demo_adjustment("laura", EVENT)
    monkeypatch.setenv("DEMO_MODE", "false")
    get_settings.cache_clear()
    portfolio_service.apply_demo_adjustment("laura", EventImpactOut.model_validate(impact))
    monkeypatch.setenv("DEMO_MODE", "true")
    get_settings.cache_clear()
    assert portfolio_service.get_valued("laura").demo_adjustments == []
