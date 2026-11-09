"""Proyección con DCA (T1-14, RF-22, diseño del MVP §4.3).

Las funciones puras se comprueban con el ejemplo del contrato (`ProjectionOut.json`): 34.311,68 €,
300 €/mes y 169 meses (de noviembre de 2026 a diciembre de 2040) dan 152.181,69 € al 5,740 %.
El dorado de Laura usa el seed y los precios de `golden/portfolio_init_cases.json`.
"""

import json
from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core import clock, trace
from app.core.errors import AppError, ErrorCode
from app.main import API_PREFIX
from app.planning import projection, service
from app.portfolio import service as portfolio_service
from app.schemas.portfolio import (
    DcaAllocation,
    DcaPlanCreateRequest,
    DcaPlanStatus,
    DcaPlanUpdateRequest,
    Frequency,
    PlanUpdateRequest,
    TargetAllocation,
)
from tests.fakes.price_provider import FakePriceProvider, use_price_provider

CASES: dict[str, Any] = json.loads(
    (Path(__file__).parent / "golden" / "portfolio_init_cases.json").read_text(encoding="utf-8")
)
NOW = datetime.fromisoformat(CASES["now"])  # 2026-11-08T18:00:00Z
D = Decimal

BASE = {"equity": D("0.0670"), "fixed_income": D("0.0350"), "cash": D("0.0180")}


@pytest.fixture(autouse=True)
def _prices() -> Iterator[None]:
    clock.set_now(NOW)
    with use_price_provider(FakePriceProvider(closes=CASES["closes"], fx=CASES["fx"])):
        yield


@pytest.fixture
def seeded(db: None) -> None:
    portfolio_service.load_seed(force=True)


def _target(equity: str, fixed_income: str, cash: str = "0") -> TargetAllocation:
    return TargetAllocation(equity=D(equity), fixed_income=D(fixed_income), cash=D(cash))


# --- Funciones puras ---


@pytest.mark.parametrize(
    ("now", "goal_year", "months"),
    [
        (datetime(2026, 11, 8, tzinfo=UTC), 2040, 169),
        (datetime(2026, 1, 1, tzinfo=UTC), 2026, 11),
        (datetime(2026, 12, 31, tzinfo=UTC), 2026, 0),
        (datetime(2026, 11, 8, tzinfo=UTC), 2025, 0),
    ],
)
def test_months_until_end_of_goal_year(now: datetime, goal_year: int, months: int) -> None:
    assert projection.months_until_goal(now, goal_year) == months


def test_blended_return_weights_by_target_allocation() -> None:
    # 0,70 × 6,70 % + 0,30 × 3,50 % = 5,740 %
    assert projection.blended_return(_target("0.70", "0.30"), BASE) == D("0.05740")


def test_blended_return_includes_cash() -> None:
    # 0,50 × 6,70 % + 0,30 × 3,50 % + 0,20 × 1,80 % = 4,760 %
    assert projection.blended_return(_target("0.50", "0.30", "0.20"), BASE) == D("0.04760")


@pytest.mark.parametrize(
    ("annual_return", "expected"),
    [
        ("0.03747", "123926.90"),
        ("0.05740", "152181.69"),
        ("0.07733", "187321.51"),
    ],
)
def test_future_value_matches_contract_example(annual_return: str, expected: str) -> None:
    value = projection.future_value(D("34311.68"), D("300.00"), D(annual_return), 169)
    assert value == D(expected)


def test_future_value_without_months_is_current_value() -> None:
    assert projection.future_value(D("1000.00"), D("300.00"), D("0.05"), 0) == D("1000.00")


def test_future_value_without_return_adds_contributions() -> None:
    assert projection.future_value(D("1000.00"), D("100.00"), D("0"), 12) == D("2200.00")


def test_monthly_contribution_sums_active_plans_and_converts_weekly() -> None:
    plans = [
        (D("300.00"), Frequency.MONTHLY, True),
        (D("50.00"), Frequency.WEEKLY, True),  # 50 × 52 / 12 = 216,67
        (D("999.00"), Frequency.MONTHLY, False),  # pausado: no cuenta
    ]
    assert projection.monthly_contribution(plans) == D("516.67")


def test_gap_is_zero_when_base_reaches_goal() -> None:
    assert projection.gap(D("150000.00"), D("152181.69")) == D("0.00")
    assert projection.gap(D("150000.00"), D("123926.90")) == D("26073.10")


# --- Servicio: dorado de Laura ---


def test_laura_is_on_track(seeded: None) -> None:
    result = service.get_projection("laura")
    valued = portfolio_service.get_valued("laura")

    assert result.goal_amount_eur == D("150000.00")
    assert result.goal_year == 2040
    assert result.current_value_eur == valued.total_eur
    assert result.monthly_contribution_eur == D("300.00")
    assert [s.name for s in result.scenarios] == ["pesimista", "base", "optimista"]
    base = result.scenarios[1]
    assert base.annual_return == D("0.05740")
    assert base.value_at_goal_eur == projection.future_value(
        valued.total_eur, D("300.00"), D("0.05740"), 169
    )
    assert base.reaches_goal is True
    assert result.on_track is True
    assert result.gap_eur == D("0.00")
    assert result.scenarios[0].reaches_goal is False  # pesimista, como en el contrato
    assert result.scenarios[2].reaches_goal is True


def test_scenarios_use_assumptions_by_class(seeded: None) -> None:
    result = service.get_projection("laura")
    # 0,70 × 4,17 % + 0,30 × 2,76 % y 0,70 × 9,23 % + 0,30 × 4,24 %
    assert result.scenarios[0].annual_return == D("0.03747")
    assert result.scenarios[2].annual_return == D("0.07733")


def test_projection_cites_assumptions_and_leaves_trace(seeded: None) -> None:
    result = service.get_projection("laura")

    source = result.assumptions_source
    assert source.kind == "assumption"
    assert source.ref == "data/seed/assumptions.json"
    assert source.as_of == datetime(2025, 12, 31, tzinfo=UTC)

    record = trace.get(result.calc_id)
    assert record is not None
    assert record.kind == "projection"
    assert record.inputs["months"] == 169
    assert record.inputs["monthly_contribution_eur"] == "300.00"
    assert record.outputs["on_track"] is True
    assert len(record.parent_calc_ids) == 2  # valoración y plan
    assert {s["kind"] for s in record.sources} == {"assumption", "user_input"}


def test_off_track_reports_gap(seeded: None) -> None:
    portfolio_service.update_plan(
        "laura",
        PlanUpdateRequest(
            target=_target("0.70", "0.30"), goal_amount_eur=D("900000.00"), goal_year=2040
        ),
    )
    result = service.get_projection("laura")
    base = result.scenarios[1]
    assert result.on_track is False
    assert base.reaches_goal is False
    assert result.gap_eur == D("900000.00") - base.value_at_goal_eur


def test_paused_dca_does_not_contribute(seeded: None) -> None:
    for plan in portfolio_service.list_dca_plans("laura"):
        portfolio_service.update_dca_plan(
            "laura", plan.id, DcaPlanUpdateRequest(status=DcaPlanStatus.PAUSED)
        )
    assert service.get_projection("laura").monthly_contribution_eur == D("0.00")


def test_several_active_plans_add_up(seeded: None) -> None:
    portfolio_service.create_dca_plan(
        "laura",
        DcaPlanCreateRequest(
            amount_eur=D("100.00"),
            frequency=Frequency.MONTHLY,
            day=20,
            allocations=[DcaAllocation(asset_id="IE00B03HD191", weight=D("1"))],
        ),
    )
    assert service.get_projection("laura").monthly_contribution_eur == D("400.00")


def test_plan_without_goal_is_404(seeded: None) -> None:
    portfolio_service.update_plan(
        "laura",
        PlanUpdateRequest(target=_target("0.70", "0.30"), goal_amount_eur=None, goal_year=None),
    )
    with pytest.raises(AppError) as exc:
        service.get_projection("laura")
    assert exc.value.code == ErrorCode.NOT_FOUND
    assert exc.value.details == {"portfolio_id": "laura", "missing": "goal"}


def test_unknown_portfolio_is_404(seeded: None) -> None:
    with pytest.raises(AppError) as exc:
        service.get_projection("nadie")
    assert exc.value.code == ErrorCode.NOT_FOUND


def test_api_returns_projection(seeded: None) -> None:
    from app.main import create_app

    with TestClient(create_app()) as client:
        response = client.get(f"{API_PREFIX}/portfolios/laura/projection")
        missing = client.get(f"{API_PREFIX}/portfolios/nadie/projection")

    assert response.status_code == 200
    body = response.json()
    assert body["on_track"] is True
    assert body["monthly_contribution_eur"] == "300.00"
    assert body["calc_id"].startswith("calc_")
    assert missing.status_code == 404
