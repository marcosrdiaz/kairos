"""Plan de inversión y variación de valor (T1-07, RF-22).

Reloj fijo en el domingo 2026-11-08 18:00 UTC y precios de `golden/portfolio_init_cases.json`
(cierres del 30-oct y del 6-nov). Con esos precios Laura tiene un 71,51 % en renta variable
frente a un objetivo del 70 %.
"""

import json
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core import clock, trace
from app.core.errors import AppError, ErrorCode
from app.main import API_PREFIX
from app.portfolio import plan, service, value_change
from app.portfolio.value_change import TxIn
from app.schemas.common import AssetClass
from app.schemas.portfolio import PlanUpdateRequest, TargetAllocation, TransactionRequest
from tests.fakes.price_provider import FakePriceProvider, use_price_provider

CASES: dict[str, Any] = json.loads(
    (Path(__file__).parent / "golden" / "portfolio_init_cases.json").read_text(encoding="utf-8")
)
NOW = datetime.fromisoformat(CASES["now"])  # 2026-11-08T18:00:00Z
WEEK_AGO = NOW - timedelta(days=7)
MSCI_EUR, IWDA = "IE00B03HD191", "IE00B4L5Y983"
D = Decimal


@pytest.fixture(autouse=True)
def _prices() -> Iterator[None]:
    clock.set_now(NOW)
    with use_price_provider(FakePriceProvider(closes=CASES["closes"], fx=CASES["fx"])):
        yield


@pytest.fixture
def seeded(db: None) -> None:
    service.load_seed(force=True)


def _target(equity: str, fixed_income: str, cash: str = "0") -> TargetAllocation:
    return TargetAllocation(equity=D(equity), fixed_income=D(fixed_income), cash=D(cash))


# --- Asignación actual y desviación (puro) ---


def test_current_allocation_by_class() -> None:
    current = plan.current_allocation(
        {AssetClass.EQUITY: D("700"), AssetClass.FIXED_INCOME: D("200"), AssetClass.CASH: D("100")}
    )
    assert current == _target("0.7000", "0.2000", "0.1000")


def test_mixed_counts_half_equity_half_fixed_income() -> None:
    current = plan.current_allocation({AssetClass.EQUITY: D("500"), AssetClass.MIXED: D("500")})
    assert current == _target("0.7500", "0.2500", "0.0000")


def test_current_allocation_of_empty_portfolio_is_zero() -> None:
    assert plan.current_allocation({}) == _target("0", "0", "0")


def test_drift_within_threshold() -> None:
    check = plan.assess(_target("0.70", "0.30"), D("0.10"), _target("0.7151", "0.2849"))
    assert check.drift_equity == D("0.0151")
    assert check.drift_exceeded is False


@pytest.mark.parametrize("equity", ["0.8100", "0.5900"])
def test_drift_beyond_threshold_either_way(equity: str) -> None:
    check = plan.assess(_target("0.70", "0.30"), D("0.10"), _target(equity, "0"))
    assert check.drift_exceeded is True


def test_drift_equal_to_threshold_is_not_exceeded() -> None:
    check = plan.assess(_target("0.70", "0.30"), D("0.10"), _target("0.8000", "0.2000"))
    assert check.drift_equity == D("0.1000")
    assert check.drift_exceeded is False


def test_empty_portfolio_has_no_drift() -> None:
    check = plan.assess(_target("0.70", "0.30"), D("0.10"), _target("0", "0", "0"))
    assert check.drift_equity == D(0)
    assert check.drift_exceeded is False


# --- get_plan / update_plan ---


def test_laura_plan_matches_seed_and_valuation(seeded: None) -> None:
    out = service.get_plan("laura")
    assert out.target == _target("0.70", "0.30", "0.00")
    assert out.drift_threshold == D("0.10")
    assert (out.goal_amount_eur, out.goal_year) == (D("150000.00"), 2040)
    assert out.current == _target("0.7151", "0.2849", "0.0000")
    assert out.drift_equity == D("0.0151")
    assert out.drift_exceeded is False


def test_plan_is_traced_from_valuation(seeded: None) -> None:
    out = service.get_plan("laura")
    record = trace.get(out.calc_id)
    assert record is not None
    assert record.kind == "plan"
    assert record.outputs["drift_equity"] == "0.0151"
    assert len(record.parent_calc_ids) == 1
    parent = trace.get(record.parent_calc_ids[0])
    assert parent is not None and parent.kind == "valuation"


def test_javier_pension_plan_splits_between_equity_and_bonds(seeded: None) -> None:
    out = service.get_plan("javier")
    valued = service.get_valued("javier")
    mixed = valued.allocation.mixed
    assert mixed > 0
    assert abs(out.current.equity - (valued.allocation.equity + mixed / 2)) <= D("0.0001")
    assert out.current.cash == valued.allocation.cash


def test_unknown_portfolio_plan_is_not_found(db: None) -> None:
    with pytest.raises(AppError) as exc:
        service.get_plan("nadie")
    assert exc.value.code is ErrorCode.NOT_FOUND


def test_update_plan_persists_and_recomputes_drift(seeded: None) -> None:
    out = service.update_plan(
        "laura", PlanUpdateRequest(target=_target("0.50", "0.50"), drift_threshold=D("0.05"))
    )
    assert out.target == _target("0.50", "0.50")
    assert out.drift_equity == D("0.2151")
    assert out.drift_exceeded is True
    again = service.get_plan("laura")
    assert again.target == out.target and again.drift_threshold == D("0.05")


def test_update_plan_keeps_fields_not_sent(seeded: None) -> None:
    request = PlanUpdateRequest.model_validate(
        {"target": {"equity": "0.6", "fixed_income": "0.4", "cash": "0"}}
    )
    out = service.update_plan("laura", request)
    assert (out.goal_amount_eur, out.goal_year) == (D("150000.00"), 2040)
    assert out.drift_threshold == D("0.10")


def test_update_plan_rejects_target_not_summing_one(seeded: None) -> None:
    with pytest.raises(AppError) as exc:
        service.update_plan("laura", PlanUpdateRequest(target=_target("0.70", "0.20")))
    assert exc.value.code is ErrorCode.VALIDATION_ERROR
    assert service.get_plan("laura").target == _target("0.70", "0.30")


@pytest.mark.parametrize("threshold", ["0", "-0.1", "1.5"])
def test_update_plan_rejects_bad_threshold(seeded: None, threshold: str) -> None:
    request = PlanUpdateRequest(target=_target("0.7", "0.3"), drift_threshold=D(threshold))
    with pytest.raises(AppError) as exc:
        service.update_plan("laura", request)
    assert exc.value.code is ErrorCode.VALIDATION_ERROR


def test_update_unknown_portfolio_is_not_found(db: None) -> None:
    with pytest.raises(AppError) as exc:
        service.update_plan("nadie", PlanUpdateRequest(target=_target("0.7", "0.3")))
    assert exc.value.code is ErrorCode.NOT_FOUND


def test_plan_endpoints(client: TestClient) -> None:
    url = f"{API_PREFIX}/portfolios/laura/plan"
    body = client.get(url).json()
    assert body["target"]["equity"] == "0.70"
    assert body["calc_id"].startswith("calc_")
    assert body["drift_exceeded"] is False
    put = client.put(url, json={"target": {"equity": "0.8", "fixed_income": "0.3", "cash": "0"}})
    assert put.status_code == 422
    assert put.json()["code"] == "VALIDATION_ERROR"
    ok = client.put(url, json={"target": {"equity": "0.6", "fixed_income": "0.4", "cash": "0"}})
    assert ok.status_code == 200
    assert ok.json()["target"]["equity"] == "0.6"


# --- Variación de valor (puro) ---


def _tx(asset: str, day: int, kind: str, units: str, amount: str) -> TxIn:
    ts = datetime(2026, 11, day, 12, tzinfo=UTC)
    return TxIn(asset_id=asset, ts=ts, type=kind, units=D(units), amount_eur=D(amount))


TXS = [
    _tx("A", 1, "initial", "10", "100.00"),
    _tx("A", 3, "buy", "5", "60.00"),
    _tx("A", 5, "sell", "2", "25.00"),
    _tx("B", 4, "dca_buy", "1", "30.00"),
    _tx("C", 2, "transfer_out", "3", "40.00"),
    _tx("D", 2, "transfer_in", "4", "40.00"),
]


def test_units_at_counts_operations_up_to_the_instant() -> None:
    at = datetime(2026, 11, 3, 12, tzinfo=UTC)
    assert value_change.units_at(TXS, at) == {"A": D("15"), "C": D("-3"), "D": D("4")}


def test_flows_between_signs_and_bounds() -> None:
    start, end = datetime(2026, 11, 1, 12, tzinfo=UTC), datetime(2026, 11, 5, 12, tzinfo=UTC)
    flows = value_change.flows_between(TXS, start, end)
    assert flows == {"A": D("35.00"), "B": D("30.00"), "C": D("-40.00"), "D": D("40.00")}


# --- get_value_change ---


def test_value_change_without_flows_matches_weekly_change(seeded: None) -> None:
    out = service.get_value_change("laura", WEEK_AGO, NOW)
    valued = service.get_valued("laura")
    assert out.end_value_eur == valued.total_eur
    assert out.start_value_eur == valued.total_eur - valued.change_week_eur
    assert out.net_flows_eur == D("0.00")
    iwda = next(a for a in out.by_asset if a.asset_id == IWDA)
    assert (iwda.start_value_eur, iwda.end_value_eur) == (D("10716.00"), D("10877.88"))
    assert out.start_value_eur == sum(a.start_value_eur for a in out.by_asset)
    assert out.end_value_eur == sum(a.end_value_eur for a in out.by_asset)


def test_value_change_includes_buy_as_flow(seeded: None) -> None:
    service.register_transaction(
        "laura", TransactionRequest(type="buy", asset_id=MSCI_EUR, amount_eur=D("300.00"))
    )
    out = service.get_value_change("laura", WEEK_AGO, NOW)
    assert out.net_flows_eur == D("300.00")
    msci = next(a for a in out.by_asset if a.asset_id == MSCI_EUR)
    assert msci.flows_eur == D("300.00")
    assert out.end_value_eur == service.get_valued("laura").total_eur


def test_value_change_is_traced(seeded: None) -> None:
    out = service.get_value_change("laura", WEEK_AGO, NOW)
    record = trace.get(out.calc_id)
    assert record is not None
    assert record.kind == "move"
    assert record.outputs["end_value_eur"] == format(out.end_value_eur, "f")
    assert record.sources


def test_value_change_rejects_inverted_window(seeded: None) -> None:
    with pytest.raises(AppError) as exc:
        service.get_value_change("laura", NOW, WEEK_AGO)
    assert exc.value.code is ErrorCode.VALIDATION_ERROR


def test_value_change_without_prices_is_unavailable(seeded: None) -> None:
    with pytest.raises(AppError) as exc:
        service.get_value_change("laura", datetime(2025, 1, 1, tzinfo=UTC), NOW)
    assert exc.value.code is ErrorCode.PRICE_UNAVAILABLE


def test_value_change_unknown_portfolio(db: None) -> None:
    with pytest.raises(AppError) as exc:
        service.get_value_change("nadie", WEEK_AGO, NOW)
    assert exc.value.code is ErrorCode.NOT_FOUND
