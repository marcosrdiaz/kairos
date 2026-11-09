"""Acceso a las tablas de DCA (`dca_plan`, `dca_allocation`, `dca_execution`, `dca_execution_line`).

Todas las funciones reciben la sesión: la transacción la abre y la cierra `dca_flow.py`.
"""

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.portfolio import dca
from app.portfolio.models import DcaAllocation, DcaExecution, DcaExecutionLine, DcaPlan
from app.portfolio.repository import new_id, utc
from app.schemas import portfolio as schemas
from app.schemas.portfolio import DcaExecutionStatus, DcaPlanOut

# --- Planes ---


def get_plan(session: Session, plan_id: str) -> DcaPlan | None:
    return session.get(DcaPlan, plan_id)


def plans_of(session: Session, portfolio_id: str) -> list[DcaPlan]:
    stmt = select(DcaPlan).where(DcaPlan.portfolio_id == portfolio_id).order_by(DcaPlan.id)
    return list(session.scalars(stmt))


def active_plans(session: Session) -> list[DcaPlan]:
    stmt = (
        select(DcaPlan)
        .where(DcaPlan.status == schemas.DcaPlanStatus.ACTIVE)
        .order_by(DcaPlan.portfolio_id, DcaPlan.id)
    )
    return list(session.scalars(stmt))


def add_plan(session: Session, portfolio_id: str, **values: object) -> DcaPlan:
    row = DcaPlan(id=new_id("dca"), portfolio_id=portfolio_id, **values)
    session.add(row)
    session.flush()
    return row


def allocations(session: Session, plan_id: str) -> list[dca.Allocation]:
    """Reparto del plan en el orden de `dca.ordered`."""
    stmt = select(DcaAllocation).where(DcaAllocation.dca_plan_id == plan_id)
    return dca.ordered([(row.asset_id, row.weight) for row in session.scalars(stmt)])


def set_allocations(session: Session, plan_id: str, values: Sequence[dca.Allocation]) -> None:
    session.execute(delete(DcaAllocation).where(DcaAllocation.dca_plan_id == plan_id))
    for asset_id, weight in values:
        session.add(DcaAllocation(dca_plan_id=plan_id, asset_id=asset_id, weight=weight))
    session.flush()


def plan_out(session: Session, row: DcaPlan) -> DcaPlanOut:
    return DcaPlanOut(
        id=row.id,
        portfolio_id=row.portfolio_id,
        amount_eur=row.amount_eur,
        frequency=schemas.Frequency(row.frequency),
        day=row.day,
        status=schemas.DcaPlanStatus(row.status),
        allocations=[
            schemas.DcaAllocation(asset_id=asset_id, weight=weight.normalize())  # 0.70000000 → 0.7
            for asset_id, weight in allocations(session, row.id)
        ],
        last_execution_at=_utc_or_none(row.last_execution_at),
        next_execution_at=_utc_or_none(row.next_execution_at),
    )


# --- Ejecuciones ---


def blocks_new_execution(session: Session, plan_id: str, scheduled_for: datetime) -> bool:
    """Hay una ejecución pendiente del plan o ya hay una para `scheduled_for` (una por fecha)."""
    stmt = select(DcaExecution).where(DcaExecution.dca_plan_id == plan_id)
    return any(
        row.status == DcaExecutionStatus.PENDING or utc(row.scheduled_for) == scheduled_for
        for row in session.scalars(stmt)
    )


def add_execution(
    session: Session,
    plan_id: str,
    scheduled_for: datetime,
    created_at: datetime,
    lines: Sequence[schemas.DcaExecutionLine],
) -> str:
    execution_id = new_id("dcx")
    session.add(
        DcaExecution(
            id=execution_id,
            dca_plan_id=plan_id,
            scheduled_for=scheduled_for,
            status=DcaExecutionStatus.PENDING,
            created_at=created_at,
            resolved_at=None,
        )
    )
    session.flush()
    for line in lines:
        session.add(
            DcaExecutionLine(
                execution_id=execution_id,
                asset_id=line.asset_id,
                amount_eur=line.amount_eur,
                price=line.price,
                price_at=line.price_at,
                units_estimated=line.units_estimated,
            )
        )
    session.flush()
    return execution_id


def get_execution(session: Session, execution_id: str) -> DcaExecution | None:
    return session.get(DcaExecution, execution_id)


def execution_lines(session: Session, execution_id: str) -> list[DcaExecutionLine]:
    """Líneas de la ejecución, en el orden del reparto (más peso primero)."""
    stmt = select(DcaExecutionLine).where(DcaExecutionLine.execution_id == execution_id)
    rows = list(session.scalars(stmt))
    return sorted(rows, key=lambda row: (-row.amount_eur, row.asset_id))


def executions_of(
    session: Session, portfolio_id: str, status: DcaExecutionStatus | None
) -> list[DcaExecution]:
    """De la más reciente a la más antigua (`scheduled_for`, después `created_at`)."""
    plan_ids = select(DcaPlan.id).where(DcaPlan.portfolio_id == portfolio_id)
    stmt = select(DcaExecution).where(DcaExecution.dca_plan_id.in_(plan_ids))
    if status is not None:
        stmt = stmt.where(DcaExecution.status == status)
    stmt = stmt.order_by(DcaExecution.scheduled_for.desc(), DcaExecution.created_at.desc())
    return list(session.scalars(stmt))


def execution_out(session: Session, row: DcaExecution) -> schemas.DcaExecutionOut:
    return schemas.DcaExecutionOut(
        id=row.id,
        dca_plan_id=row.dca_plan_id,
        scheduled_for=utc(row.scheduled_for),
        status=DcaExecutionStatus(row.status),
        lines=[
            schemas.DcaExecutionLine(
                asset_id=line.asset_id,
                amount_eur=line.amount_eur,
                price=line.price,
                price_at=utc(line.price_at),
                units_estimated=line.units_estimated,
            )
            for line in execution_lines(session, row.id)
        ],
    )


def _utc_or_none(value: datetime | None) -> datetime | None:
    return utc(value) if value is not None else None
