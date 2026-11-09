"""DCA (RF-07, UC-04, UC-12): planes, ejecuciones pendientes y confirmar o saltar.

La aritmética está en `dca.py` y `lots.py`; aquí se valida, se piden precios, se deja la traza y se
escribe. Si falta un precio (503) o algo no valida, no se guarda nada.

- Crear o editar un plan calcula `next_execution_at` desde hoy (hoy cuenta).
- `run(force=False)` es el job: crea una ejecución pendiente por cada plan activo cuya
  `next_execution_at` ya ha llegado, fechada ese día. `run(force=True)` es `/demo/dca/run`: la crea
  para hoy en todos los planes activos. En ambos casos, como mucho una pendiente por plan y una
  ejecución por fecha. Las líneas llevan el precio del momento y las participaciones estimadas.
- Confirmar compra cada línea (`dca_buy`) al precio del momento de confirmar, abre un lote por
  línea y deja una traza `dca`. Las líneas se actualizan con el precio y las participaciones
  reales. Saltar no mueve dinero.
- Al resolver, `next_execution_at` pasa a la primera fecha del plan posterior a `scheduled_for`;
  al confirmar, además, `last_execution_at = scheduled_for`.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.core import clock, trace
from app.core.db import session_scope
from app.portfolio import dca, dca_store, errors, ledger, lots, repository
from app.portfolio import quotes as pricing
from app.portfolio.engine import QuoteIn
from app.portfolio.models import DcaExecution, DcaPlan
from app.schemas.common import SourceRef, TraceKind
from app.schemas.portfolio import (
    DcaExecutionActionRequest,
    DcaExecutionLine,
    DcaExecutionOut,
    DcaExecutionStatus,
    DcaPlanCreateRequest,
    DcaPlanOut,
    DcaPlanUpdateRequest,
    Frequency,
)

# --- Planes ---


def list_plans(portfolio_id: str) -> list[DcaPlanOut]:
    with session_scope() as session:
        _require_portfolio(session, portfolio_id)
        return [
            dca_store.plan_out(session, row) for row in dca_store.plans_of(session, portfolio_id)
        ]


def create_plan(portfolio_id: str, request: DcaPlanCreateRequest) -> DcaPlanOut:
    allocations = [(a.asset_id, a.weight) for a in request.allocations]
    with session_scope() as session:
        _require_portfolio(session, portfolio_id)
        _validate(session, request.frequency, request.day, allocations)
        row = dca_store.add_plan(
            session,
            portfolio_id,
            amount_eur=request.amount_eur,
            frequency=request.frequency,
            day=request.day,
            status=request.status,
            last_execution_at=None,
            next_execution_at=_first_execution(request.frequency, request.day),
        )
        dca_store.set_allocations(session, row.id, allocations)
        return dca_store.plan_out(session, row)


def update_plan(portfolio_id: str, plan_id: str, request: DcaPlanUpdateRequest) -> DcaPlanOut:
    with session_scope() as session:
        row = dca_store.get_plan(session, plan_id)
        if row is None or row.portfolio_id != portfolio_id:
            raise errors.dca_plan_not_found(portfolio_id, plan_id)
        frequency = request.frequency or Frequency(row.frequency)
        day = request.day if request.day is not None else row.day
        allocations = (
            [(a.asset_id, a.weight) for a in request.allocations]
            if request.allocations is not None
            else dca_store.allocations(session, plan_id)
        )
        _validate(session, frequency, day, allocations)
        if request.amount_eur is not None:
            row.amount_eur = request.amount_eur
        if request.status is not None:
            row.status = request.status
        schedule_changed = (frequency, day) != (Frequency(row.frequency), row.day)
        row.frequency, row.day = frequency, day
        current = row.next_execution_at
        if schedule_changed or current is None or repository.utc(current) < _today():
            row.next_execution_at = _first_execution(frequency, day)
        if request.allocations is not None:
            dca_store.set_allocations(session, plan_id, allocations)
        session.flush()
        return dca_store.plan_out(session, row)


# --- Ejecuciones ---


@dataclass(frozen=True)
class _Due:
    plan_id: str
    scheduled_for: datetime
    amounts: list[dca.Allocation]


def run(force: bool) -> list[DcaExecutionOut]:
    """Crea las ejecuciones pendientes que tocan y las devuelve (ver el docstring del módulo)."""
    now = clock.now()
    with session_scope() as session:
        due = [
            item
            for row in dca_store.active_plans(session)
            if (item := _due(session, row, now, force)) is not None
        ]
    if not due:
        return []
    quotes, _ = pricing.quotes({asset_id for item in due for asset_id, _ in item.amounts})
    with session_scope() as session:
        created = []
        for item in due:
            lines = []
            for asset_id, amount in item.amounts:
                quote = quotes[asset_id]
                trade = lots.size_trade(quote.price, quote.fx_rate, amount_eur=amount)
                lines.append(
                    DcaExecutionLine(
                        asset_id=asset_id,
                        amount_eur=trade.amount_eur,
                        price=quote.price,
                        price_at=quote.price_at,
                        units_estimated=trade.units,
                    )
                )
            execution_id = dca_store.add_execution(
                session, item.plan_id, item.scheduled_for, now, lines
            )
            created.append(execution_id)
        return [_execution_out(session, execution_id) for execution_id in created]


def list_executions(portfolio_id: str, status: DcaExecutionStatus | None) -> list[DcaExecutionOut]:
    with session_scope() as session:
        _require_portfolio(session, portfolio_id)
        rows = dca_store.executions_of(session, portfolio_id, status)
        return [dca_store.execution_out(session, row) for row in rows]


def act(execution_id: str, request: DcaExecutionActionRequest) -> DcaExecutionOut:
    """Confirma (compra al precio de ahora) o salta una ejecución pendiente."""
    with session_scope() as session:
        _pending(session, execution_id)  # 404 o 422 antes de pedir precios
        asset_ids = [line.asset_id for line in dca_store.execution_lines(session, execution_id)]
    confirm = request.action == "confirm"
    quoted = pricing.quotes(asset_ids) if confirm else None  # 503 antes de escribir nada
    with session_scope() as session:
        execution, plan = _pending(session, execution_id)
        if quoted is not None:
            _buy_lines(session, execution, plan, *quoted)
            plan.last_execution_at = repository.utc(execution.scheduled_for)
        execution.status = DcaExecutionStatus.CONFIRMED if confirm else DcaExecutionStatus.SKIPPED
        execution.resolved_at = clock.now()
        plan.next_execution_at = dca.next_execution(
            Frequency(plan.frequency),
            plan.day,
            repository.utc(execution.scheduled_for),
            inclusive=False,
        )
        session.flush()
        return dca_store.execution_out(session, execution)


def _pending(session: Session, execution_id: str) -> tuple[DcaExecution, DcaPlan]:
    execution = dca_store.get_execution(session, execution_id)
    if execution is None:
        raise errors.dca_execution_not_found(execution_id)
    if execution.status != DcaExecutionStatus.PENDING:
        raise errors.dca_execution_resolved(execution_id, execution.status)
    plan = dca_store.get_plan(session, execution.dca_plan_id)
    assert plan is not None  # FK
    return execution, plan


def _buy_lines(
    session: Session,
    execution: DcaExecution,
    plan: DcaPlan,
    quotes: dict[str, QuoteIn],
    sources: list[SourceRef],
) -> None:
    """Un `dca_buy` y un lote por línea, con una traza `dca` común."""
    now = clock.now()
    bought = []
    for line in dca_store.execution_lines(session, execution.id):
        quote = quotes[line.asset_id]
        trade = lots.size_trade(quote.price, quote.fx_rate, amount_eur=line.amount_eur)
        held = ledger.asset_lots(session, plan.portfolio_id, line.asset_id)
        bought.append((line, quote, trade, lots.buy(held, trade, now)))
    calc_id = trace.record(
        TraceKind.DCA,
        dca.FORMULA,
        inputs={
            "execution_id": execution.id,
            "dca_plan_id": plan.id,
            "portfolio_id": plan.portfolio_id,
            "scheduled_for": execution.scheduled_for,
            "lines": {line.asset_id: line.amount_eur for line, *_ in bought},
            "quotes": {line.asset_id: vars(quote) for line, quote, *_ in bought},
        },
        outputs={
            line.asset_id: {**vars(trade), "units_after": outcome.units_after}
            for line, _, trade, outcome in bought
        },
        sources=sources,
    )
    for line, quote, trade, outcome in bought:
        tx_id = ledger.add_transaction(
            session,
            plan.portfolio_id,
            type="dca_buy",
            asset_id=line.asset_id,
            ts=now,
            units=trade.units,
            price=quote.price,
            price_currency=quote.currency,
            fx_rate=quote.fx_rate,
            amount_eur=trade.amount_eur,
            dca_plan_id=plan.id,
            calc_id=calc_id,
        )
        for lot in outcome.created:
            ledger.add_lot(session, plan.portfolio_id, line.asset_id, lot, tx_id)
        line.transaction_id = tx_id
        line.price, line.price_at, line.units_estimated = quote.price, quote.price_at, trade.units


# --- Auxiliares ---


def _require_portfolio(session: Session, portfolio_id: str) -> None:
    if repository.get_portfolio(session, portfolio_id) is None:
        raise errors.portfolio_not_found(portfolio_id)


def _validate(
    session: Session, frequency: Frequency, day: int, allocations: list[dca.Allocation]
) -> None:
    try:
        dca.check_day(frequency, day)
    except dca.InvalidDay as exc:
        raise errors.dca_invalid_day(str(exc)) from exc
    try:
        dca.check_allocations(allocations)
    except dca.InvalidAllocation as exc:
        raise errors.dca_allocation_invalid(str(exc)) from exc
    known = repository.get_assets(session, [asset_id for asset_id, _ in allocations])
    for asset_id, _ in allocations:
        if asset_id not in known:
            raise errors.unknown_asset(asset_id)


def _today() -> datetime:
    return dca.day_start(clock.now())


def _first_execution(frequency: Frequency, day: int) -> datetime:
    return dca.next_execution(frequency, day, clock.now(), inclusive=True)


def _due(session: Session, plan: DcaPlan, now: datetime, force: bool) -> _Due | None:
    if force:
        scheduled_for = dca.day_start(now)
    elif plan.next_execution_at is None or repository.utc(plan.next_execution_at) > now:
        return None
    else:
        scheduled_for = repository.utc(plan.next_execution_at)
    if dca_store.blocks_new_execution(session, plan.id, scheduled_for):
        return None
    amounts = dca.split_amount(plan.amount_eur, dca_store.allocations(session, plan.id))
    return _Due(plan.id, scheduled_for, amounts)


def _execution_out(session: Session, execution_id: str) -> DcaExecutionOut:
    row = dca_store.get_execution(session, execution_id)
    assert row is not None
    return dca_store.execution_out(session, row)
