"""Atribución de "¿Por qué ha bajado?" (`explain_move`, T2-07; diseño del MVP §4.3)."""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core import clock, trace
from app.impact import move
from app.main import API_PREFIX
from app.portfolio import service as portfolio_service
from app.schemas.impact import MoveEventImpact

NOW = datetime(2026, 11, 8, 18, 0, tzinfo=UTC)
EVENT = "nvda-2025-02"


@pytest.fixture(autouse=True)
def _fixed_clock() -> Iterator[None]:
    clock.set_now(NOW)
    yield


def _move(client: TestClient, period: str = "week", portfolio_id: str = "laura") -> dict[str, Any]:
    response = client.get(f"{API_PREFIX}/portfolios/{portfolio_id}/move", params={"period": period})
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


def _replay(client: TestClient, event_id: str = EVENT) -> None:
    assert client.post(f"{API_PREFIX}/demo/replay/{event_id}").status_code == 200


def _d(value: str) -> Decimal:
    return Decimal(value)


# --- Motor (puro) ---


@pytest.mark.parametrize(("period", "days"), [("day", 1), ("week", 7), ("month", 30)])
def test_window_ends_now_and_spans_the_period(period: move.MovePeriod, days: int) -> None:
    assert move.window(period, NOW) == (NOW - timedelta(days=days), NOW)


def _asset(asset_id: str, start: str, end: str, flows: str = "0", adj: str = "0") -> move.AssetIn:
    return move.AssetIn(asset_id, f"Activo {asset_id}", _d(start), _d(end), _d(flows), _d(adj))


def _event(event_id: str, impact: str) -> MoveEventImpact:
    return MoveEventImpact(
        event_id=event_id,
        title=event_id,
        impact_eur=_d(impact),
        low_eur=_d(impact) * 2,
        high_eur=Decimal(0),
    )


def test_attribute_removes_flows_and_adds_demo_adjustments() -> None:
    result = move.attribute(
        [
            _asset("A", "1000.00", "1250.00", flows="300.00"),  # compra de 300: cambia -50
            _asset("B", "2000.00", "2000.00", adj="-30.00"),  # solo el ajuste de demo
        ],
        [],
    )
    by_asset = {a.asset_id: a.change_eur for a in result.by_asset}
    assert by_asset == {"A": _d("-50.00"), "B": _d("-30.00")}
    assert result.change_eur == _d("-80.00")
    assert result.change_pct == _d("-0.0267")  # -80 / 3000


def test_attribute_sorts_by_size_and_omits_unchanged_assets() -> None:
    result = move.attribute(
        [
            _asset("A", "100.00", "110.00"),
            _asset("B", "100.00", "100.00"),
            _asset("C", "100.00", "50.00"),
        ],
        [],
    )
    assert [a.asset_id for a in result.by_asset] == ["C", "A"]
    assert result.by_asset[0].name == "Activo C"


def test_unexplained_is_change_minus_event_estimates() -> None:
    result = move.attribute(
        [_asset("A", "1000.00", "900.00")], [_event("e1", "-70.00"), _event("e2", "-10.00")]
    )
    assert result.change_eur == _d("-100.00")
    assert result.unexplained_eur == _d("-20.00")


def test_change_pct_is_zero_without_starting_value() -> None:
    result = move.attribute([_asset("A", "0", "500.00", flows="500.00", adj="-5.00")], [])
    assert result.change_eur == _d("-5.00")
    assert result.change_pct == _d("0.0000")


# --- Servicio y API ---


def test_move_without_events_is_the_real_value_change(client: TestClient) -> None:
    body = _move(client)
    start, end = NOW - timedelta(days=7), NOW
    change = portfolio_service.get_value_change("laura", start, end)
    expected = change.end_value_eur - change.start_value_eur - change.net_flows_eur
    assert body["period"] == "week"
    assert _d(body["change_eur"]) == expected
    assert sum(_d(a["change_eur"]) for a in body["by_asset"]) == expected
    assert body["by_event"] == []
    assert _d(body["unexplained_eur"]) == expected
    assert all(a["name"] for a in body["by_asset"])


def test_move_leaves_a_traceable_record(client: TestClient) -> None:
    body = _move(client)
    record = trace.get(body["calc_id"])
    assert record is not None
    assert record.kind == "move"
    assert _d(record.outputs["change_eur"]) == _d(body["change_eur"])
    assert record.parent_calc_ids  # apunta al `get_value_change`
    parent = trace.get(record.parent_calc_ids[0])
    assert parent is not None and parent.kind == "move"


def test_move_after_replay_includes_the_event_and_its_demo_adjustment(
    client: TestClient,
) -> None:
    before = _move(client)
    _replay(client)
    after = _move(client)
    impact = next(
        e
        for e in client.get(f"{API_PREFIX}/portfolios/laura/events").json()
        if e["event_id"] == EVENT
    )
    held = {p["asset_id"] for p in client.get(f"{API_PREFIX}/portfolios/laura").json()["positions"]}
    adjustment = sum(_d(a["impact_eur"]) for a in impact["breakdown"] if a["asset_id"] in held)

    assert adjustment != 0
    assert _d(after["change_eur"]) - _d(before["change_eur"]) == adjustment
    assert sum(_d(a["change_eur"]) for a in after["by_asset"]) == _d(after["change_eur"])
    assert [e["event_id"] for e in after["by_event"]] == [EVENT]
    event = after["by_event"][0]
    assert event["title"] == impact["title"]
    assert (event["impact_eur"], event["low_eur"], event["high_eur"]) == (
        impact["impact_eur"],
        impact["low_eur"],
        impact["high_eur"],
    )
    assert _d(after["unexplained_eur"]) == _d(after["change_eur"]) - _d(impact["impact_eur"])
    record = trace.get(after["calc_id"])
    assert record is not None and impact["calc_id"] in record.parent_calc_ids


def test_event_outside_the_period_is_left_out_with_its_adjustment(client: TestClient) -> None:
    clock.set_now(NOW - timedelta(days=3))
    _replay(client)
    clock.set_now(NOW)
    day = _move(client, "day")
    week = _move(client, "week")
    assert day["by_event"] == []
    assert [e["event_id"] for e in week["by_event"]] == [EVENT]
    change = portfolio_service.get_value_change("laura", NOW - timedelta(days=1), NOW)
    assert _d(day["change_eur"]) == (
        change.end_value_eur - change.start_value_eur - change.net_flows_eur
    )


def test_move_unknown_portfolio_is_404(client: TestClient) -> None:
    assert client.get(f"{API_PREFIX}/portfolios/nadie/move").status_code == 404


def test_move_rejects_unknown_period(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/portfolios/laura/move", params={"period": "year"})
    assert response.status_code == 422
