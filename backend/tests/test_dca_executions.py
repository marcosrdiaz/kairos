"""Ejecuciones DCA (T1-06, RF-07, UC-12): `/demo/dca/run`, job, confirmar o saltar.

Precios fijos de `golden/portfolio_init_cases.json` (reloj 2026-11-08 18:00 UTC). Cifras
esperadas calculadas a mano: `units = amount_eur / (price × fx)` a 8 decimales, HALF_EVEN.
Laura: 300 € al mes el día 5, 70/30 entre IE00B03HD191 (48,20) e IE00B18GC888 (95,10).
Javier: 200 € al mes el día 10, todo a IE0007472115 (236,40).
"""

import json
from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core import clock, trace
from app.core.db import session_scope
from app.core.errors import AppError, ErrorCode
from app.main import API_PREFIX
from app.portfolio import service
from app.portfolio.models import Transaction
from app.schemas.common import TraceKind
from app.schemas.portfolio import (
    DcaAllocation,
    DcaExecutionActionRequest,
    DcaExecutionStatus,
    DcaPlanCreateRequest,
    DcaPlanUpdateRequest,
    Frequency,
)
from tests.fakes.price_provider import FakePriceProvider, use_price_provider

PRICES: dict[str, Any] = json.loads(
    (Path(__file__).parent / "golden" / "portfolio_init_cases.json").read_text(encoding="utf-8")
)
NOW = datetime.fromisoformat(PRICES["now"])  # 2026-11-08T18:00:00Z
TODAY = datetime(2026, 11, 8, tzinfo=UTC)
MSCI_EUR, BONDS, EUROSTOXX = "IE00B03HD191", "IE00B18GC888", "IE0007472115"
CONFIRM = DcaExecutionActionRequest(action="confirm")
SKIP = DcaExecutionActionRequest(action="skip")


@pytest.fixture(autouse=True)
def _prices() -> Iterator[None]:
    clock.set_now(NOW)
    with use_price_provider(FakePriceProvider(closes=PRICES["closes"], fx=PRICES["fx"])):
        yield


@pytest.fixture
def seeded(db: None) -> None:
    service.load_seed(force=True)


def _alloc(*pairs: tuple[str, str]) -> list[DcaAllocation]:
    return [DcaAllocation(asset_id=a, weight=Decimal(w)) for a, w in pairs]


def _units(portfolio_id: str, asset_id: str) -> Decimal:
    positions = service.get_valued(portfolio_id).positions
    return next(p.units for p in positions if p.asset_id == asset_id)


def _dca_transactions(portfolio_id: str) -> list[Transaction]:
    with session_scope() as session:
        stmt = select(Transaction).where(
            Transaction.portfolio_id == portfolio_id, Transaction.type == "dca_buy"
        )
        rows = list(session.scalars(stmt))
        session.expunge_all()
        return rows


def _error(exc: pytest.ExceptionInfo[AppError]) -> ErrorCode:
    return exc.value.code


# --- Ejecuciones ---


def test_demo_run_creates_pending_executions_for_today(seeded: None) -> None:
    executions = {e.dca_plan_id: e for e in service.run_dca_demo()}
    assert set(executions) == {"dca_laura", "dca_javier", "dca_victor"}
    laura = executions["dca_laura"].model_dump(mode="json")
    assert laura["id"].startswith("dcx_")
    assert laura["scheduled_for"] == "2026-11-08T00:00:00Z"
    assert laura["status"] == "pending"
    assert [
        {k: line[k] for k in ("asset_id", "amount_eur", "price", "units_estimated")}
        for line in laura["lines"]
    ] == [
        {
            "asset_id": MSCI_EUR,
            "amount_eur": "210.00",
            "price": "48.20000000",
            "units_estimated": "4.35684647",
        },
        {
            "asset_id": BONDS,
            "amount_eur": "90.00",
            "price": "95.10000000",
            "units_estimated": "0.94637224",
        },
    ]
    assert laura["lines"][0]["price_at"].startswith("2026-11-06")
    (javier_line,) = executions["dca_javier"].lines
    assert javier_line.amount_eur == Decimal("200.00")
    assert javier_line.units_estimated == Decimal("0.84602369")


def test_demo_run_is_idempotent_and_skips_paused_plans(seeded: None) -> None:
    service.update_dca_plan("javier", "dca_javier", DcaPlanUpdateRequest(status="paused"))
    assert [e.dca_plan_id for e in service.run_dca_demo()] == ["dca_laura", "dca_victor"]
    assert service.run_dca_demo() == []
    assert len(service.list_dca_executions("laura")) == 1
    assert service.list_dca_executions("javier") == []


def test_demo_run_does_not_repeat_a_resolved_day(seeded: None) -> None:
    (execution,) = (e for e in service.run_dca_demo() if e.dca_plan_id == "dca_laura")
    service.act_on_dca_execution(execution.id, SKIP)
    assert all(e.dca_plan_id != "dca_laura" for e in service.run_dca_demo())


def test_due_run_only_creates_plans_whose_day_has_come(seeded: None) -> None:
    assert service.run_dca_due() == []
    clock.set_now(datetime(2026, 11, 10, 9, tzinfo=UTC))
    (execution,) = service.run_dca_due()
    assert execution.dca_plan_id == "dca_javier"
    assert execution.scheduled_for == datetime(2026, 11, 10, tzinfo=UTC)
    assert service.run_dca_due() == []


def test_split_gives_rounding_remainder_to_first_line(seeded: None) -> None:
    """10,01 € al 50/50: 5,005 → 5,00 con HALF_EVEN en cada línea; el céntimo que falta va a la
    primera (más peso; si empatan, menor `asset_id`) para que la suma sea el importe del plan."""
    request = DcaPlanCreateRequest(
        amount_eur=Decimal("10.01"),
        frequency=Frequency.MONTHLY,
        day=8,
        allocations=_alloc((BONDS, "0.5"), (MSCI_EUR, "0.5")),
    )
    plan = service.create_dca_plan("laura", request)
    (execution,) = (e for e in service.run_dca_demo() if e.dca_plan_id == plan.id)
    assert [(line.asset_id, line.amount_eur) for line in execution.lines] == [
        (MSCI_EUR, Decimal("5.01")),
        (BONDS, Decimal("5.00")),
    ]


def test_list_executions_filters_and_orders(seeded: None) -> None:
    (first,) = (e for e in service.run_dca_demo() if e.dca_plan_id == "dca_laura")
    service.act_on_dca_execution(first.id, SKIP)
    clock.set_now(datetime(2026, 11, 9, 10, tzinfo=UTC))
    (second,) = (e for e in service.run_dca_demo() if e.dca_plan_id == "dca_laura")
    assert [e.id for e in service.list_dca_executions("laura")] == [second.id, first.id]
    pending = service.list_dca_executions("laura", DcaExecutionStatus.PENDING)
    assert [e.id for e in pending] == [second.id]
    skipped = service.list_dca_executions("laura", DcaExecutionStatus.SKIPPED)
    assert [e.id for e in skipped] == [first.id]


def test_confirm_buys_each_line_at_todays_price(seeded: None) -> None:
    before = {a: _units("laura", a) for a in (MSCI_EUR, BONDS)}
    (execution,) = (e for e in service.run_dca_demo() if e.dca_plan_id == "dca_laura")
    out = service.act_on_dca_execution(execution.id, CONFIRM)
    assert out.status is DcaExecutionStatus.CONFIRMED
    assert _units("laura", MSCI_EUR) == before[MSCI_EUR] + Decimal("4.35684647")
    assert _units("laura", BONDS) == before[BONDS] + Decimal("0.94637224")
    txs = sorted(_dca_transactions("laura"), key=lambda tx: tx.asset_id)
    assert [(tx.asset_id, tx.amount_eur, tx.units) for tx in txs] == [
        (MSCI_EUR, Decimal("210.00"), Decimal("4.35684647")),
        (BONDS, Decimal("90.00"), Decimal("0.94637224")),
    ]
    assert all(tx.dca_plan_id == "dca_laura" for tx in txs)
    record = trace.get(txs[0].calc_id or "")
    assert record is not None
    assert record.kind == TraceKind.DCA
    (plan,) = service.list_dca_plans("laura")
    assert plan.last_execution_at == TODAY
    assert plan.next_execution_at == datetime(2026, 12, 5, tzinfo=UTC)
    assert service.list_dca_executions("laura", DcaExecutionStatus.PENDING) == []


def test_confirm_uses_price_at_confirmation(seeded: None) -> None:
    (execution,) = (e for e in service.run_dca_demo() if e.dca_plan_id == "dca_javier")
    closes = {**PRICES["closes"], EUROSTOXX: {"2026-11-06": "236.40", "2026-11-09": "200.00"}}
    clock.set_now(datetime(2026, 11, 9, 18, tzinfo=UTC))
    with use_price_provider(FakePriceProvider(closes=closes, fx=PRICES["fx"])):
        out = service.act_on_dca_execution(execution.id, CONFIRM)
    (line,) = out.lines
    assert line.price == Decimal("200.00")
    assert line.units_estimated == Decimal("1.00000000")
    (tx,) = _dca_transactions("javier")
    assert tx.units == Decimal("1.00000000")


def test_skip_moves_no_money_and_advances_next_execution(seeded: None) -> None:
    before = service.get_valued("javier").total_eur
    (execution,) = (e for e in service.run_dca_demo() if e.dca_plan_id == "dca_javier")
    out = service.act_on_dca_execution(execution.id, SKIP)
    assert out.status is DcaExecutionStatus.SKIPPED
    assert _dca_transactions("javier") == []
    assert service.get_valued("javier").total_eur == before
    (plan,) = service.list_dca_plans("javier")
    assert plan.last_execution_at == datetime(2026, 10, 10, tzinfo=UTC)
    assert plan.next_execution_at == datetime(2026, 11, 10, tzinfo=UTC)


def test_due_execution_advances_next_execution_after_confirm(seeded: None) -> None:
    clock.set_now(datetime(2026, 11, 10, 9, tzinfo=UTC))
    (execution,) = service.run_dca_due()
    service.act_on_dca_execution(execution.id, CONFIRM)
    (plan,) = service.list_dca_plans("javier")
    assert plan.last_execution_at == datetime(2026, 11, 10, tzinfo=UTC)
    assert plan.next_execution_at == datetime(2026, 12, 10, tzinfo=UTC)


@pytest.mark.parametrize("second", [CONFIRM, SKIP])
def test_resolved_execution_cannot_be_resolved_again(
    seeded: None, second: DcaExecutionActionRequest
) -> None:
    (execution,) = (e for e in service.run_dca_demo() if e.dca_plan_id == "dca_laura")
    service.act_on_dca_execution(execution.id, CONFIRM)
    with pytest.raises(AppError) as exc:
        service.act_on_dca_execution(execution.id, second)
    assert _error(exc) is ErrorCode.VALIDATION_ERROR
    assert len(_dca_transactions("laura")) == 2


def test_act_on_unknown_execution(seeded: None) -> None:
    with pytest.raises(AppError) as exc:
        service.act_on_dca_execution("dcx_nada", CONFIRM)
    assert _error(exc) is ErrorCode.NOT_FOUND


def test_run_without_price_writes_nothing(seeded: None) -> None:
    closes = {k: v for k, v in PRICES["closes"].items() if k != BONDS}
    with use_price_provider(FakePriceProvider(closes=closes, fx=PRICES["fx"])):
        with pytest.raises(AppError) as exc:
            service.run_dca_demo()
    assert _error(exc) is ErrorCode.PRICE_UNAVAILABLE
    assert service.list_dca_executions("laura") == []
    assert service.list_dca_executions("javier") == []


def test_reset_clears_executions(seeded: None) -> None:
    service.run_dca_demo()
    service.reset_demo()
    assert service.list_dca_executions("laura") == []


# --- API ---


def test_api_flow(client: TestClient) -> None:
    with use_price_provider(FakePriceProvider(closes=PRICES["closes"], fx=PRICES["fx"])):
        run = client.post(f"{API_PREFIX}/demo/dca/run")
        assert run.status_code == 200
        pending = client.get(
            f"{API_PREFIX}/portfolios/laura/dca-executions", params={"status": "pending"}
        ).json()
        assert [e["dca_plan_id"] for e in pending] == ["dca_laura"]
        done = client.post(
            f"{API_PREFIX}/dca-executions/{pending[0]['id']}", json=CONFIRM.model_dump()
        )
        assert done.status_code == 200
        assert done.json()["status"] == "confirmed"
        again = client.post(
            f"{API_PREFIX}/dca-executions/{pending[0]['id']}", json=SKIP.model_dump()
        )
        assert again.status_code == 422
