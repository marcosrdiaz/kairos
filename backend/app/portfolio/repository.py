"""Acceso a las tablas de `portfolio` (`portfolio/models.py`). Solo lo usa `portfolio/service.py`.

Todas las funciones reciben la sesión: la transacción la abre y la cierra el servicio.
"""

import uuid
from collections.abc import Iterable
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.orm import Session

from app.portfolio.engine import AssetIn
from app.portfolio.models import (
    Asset,
    DcaAllocation,
    DcaExecution,
    DcaExecutionLine,
    DcaPlan,
    DemoAdjustment,
    Plan,
    Portfolio,
    TaxLot,
    Transaction,
)
from app.schemas.common import AssetClass, AssetType, PriceKind
from app.schemas.portfolio import AssetOut

_TER_STEP = Decimal("0.0001")
_CENT = Decimal("0.01")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def utc(value: datetime) -> datetime:
    """SQLite devuelve las fechas sin zona; se guardan siempre en UTC (Postgres ya la trae)."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


# --- Activos ---


def upsert_assets(session: Session, rows: Iterable[dict[str, Any]]) -> None:
    for raw in rows:
        session.merge(
            Asset(
                id=raw["id"],
                isin=raw["isin"],
                ticker=raw["ticker"],
                name=raw["name"],
                asset_type=AssetType(raw["asset_type"]).value,
                asset_class=AssetClass(raw["asset_class"]).value,
                currency=raw["currency"],
                ter=Decimal(raw["ter"]) if raw.get("ter") is not None else None,
                transferable=bool(raw["transferable"]),
                price_kind=PriceKind(raw["price_kind"]).value,
                price_source=raw["price_source"],
            )
        )
    session.flush()


def _asset_in(row: Asset) -> AssetIn:
    return AssetIn(
        id=row.id,
        isin=row.isin,
        ticker=row.ticker,
        name=row.name,
        asset_type=AssetType(row.asset_type),
        asset_class=AssetClass(row.asset_class),
        transferable=row.transferable,
    )


def get_assets(session: Session, asset_ids: Iterable[str]) -> dict[str, AssetIn]:
    ids = set(asset_ids)
    if not ids:
        return {}
    rows = session.scalars(select(Asset).where(Asset.id.in_(ids)))
    return {row.id: _asset_in(row) for row in rows}


def _ter(value: Decimal | None) -> Decimal | None:
    """TER a 4 decimales, como en el catálogo (la columna guarda 8)."""
    return value.quantize(_TER_STEP, rounding=ROUND_HALF_EVEN) if value is not None else None


def search_assets(session: Session, query: str, limit: int) -> list[AssetOut]:
    """ISIN, ticker o nombre que contengan `query` (sin distinguir mayúsculas)."""
    pattern = f"%{query.strip().lower()}%"
    stmt = (
        select(Asset)
        .where(
            or_(
                func.lower(Asset.id).like(pattern),
                func.lower(func.coalesce(Asset.isin, "")).like(pattern),
                func.lower(func.coalesce(Asset.ticker, "")).like(pattern),
                func.lower(Asset.name).like(pattern),
            )
        )
        .order_by(Asset.name, Asset.id)
        .limit(limit)
    )
    return [
        AssetOut(
            id=row.id,
            isin=row.isin,
            ticker=row.ticker,
            name=row.name,
            asset_type=AssetType(row.asset_type),
            asset_class=AssetClass(row.asset_class),
            currency=row.currency,
            ter=_ter(row.ter),
            transferable=row.transferable,
            price_kind=PriceKind(row.price_kind),
        )
        for row in session.scalars(stmt)
    ]


# --- Carteras ---


def get_portfolio(session: Session, portfolio_id: str) -> Portfolio | None:
    return session.get(Portfolio, portfolio_id)


def list_portfolio_ids(session: Session) -> list[str]:
    """Por orden de alta (la más antigua primero)."""
    return list(session.scalars(select(Portfolio.id).order_by(Portfolio.created_at, Portfolio.id)))


def upsert_portfolio(
    session: Session,
    portfolio_id: str,
    name: str,
    profile: str,
    base_currency: str,
    now: datetime,
    *,
    kind: str | None,
    risk_profile: str | None,
) -> None:
    """Crea la fila o, si ya existe, cambia sus datos (sin tocar `created_at`)."""
    row = session.get(Portfolio, portfolio_id)
    if row is None:
        session.add(
            Portfolio(
                id=portfolio_id,
                name=name,
                profile=profile,
                kind=kind,
                risk_profile=risk_profile,
                base_currency=base_currency,
                created_at=now,
            )
        )
    else:
        row.name, row.profile, row.base_currency = name, profile, base_currency
        row.kind, row.risk_profile = kind, risk_profile
    session.flush()


def delete_portfolio(session: Session, portfolio_id: str) -> None:
    """Borra lo de `portfolio` en orden y después la fila; avisos, impactos y lo demás que cuelga
    de la cartera se van por `ON DELETE CASCADE`."""
    clear_portfolio(session, portfolio_id)
    session.execute(delete(Portfolio).where(Portfolio.id == portfolio_id))
    session.flush()


def clear_portfolio(session: Session, portfolio_id: str) -> None:
    """Borra todo lo de la cartera en las tablas de `portfolio`, menos la propia fila."""
    plan_ids = select(DcaPlan.id).where(DcaPlan.portfolio_id == portfolio_id)
    execution_ids = select(DcaExecution.id).where(DcaExecution.dca_plan_id.in_(plan_ids))
    session.execute(delete(DemoAdjustment).where(DemoAdjustment.portfolio_id == portfolio_id))
    session.execute(
        delete(DcaExecutionLine).where(DcaExecutionLine.execution_id.in_(execution_ids))
    )
    session.execute(delete(DcaExecution).where(DcaExecution.dca_plan_id.in_(plan_ids)))
    session.execute(delete(DcaAllocation).where(DcaAllocation.dca_plan_id.in_(plan_ids)))
    session.execute(delete(TaxLot).where(TaxLot.portfolio_id == portfolio_id))
    session.execute(
        update(Transaction)
        .where(Transaction.portfolio_id == portfolio_id)
        .values(linked_tx_id=None, dca_plan_id=None)
    )
    session.execute(delete(Transaction).where(Transaction.portfolio_id == portfolio_id))
    session.execute(delete(DcaPlan).where(DcaPlan.portfolio_id == portfolio_id))
    session.execute(delete(Plan).where(Plan.portfolio_id == portfolio_id))
    session.flush()


# --- Ajuste de demo (D-031) ---


def list_demo_adjustments(session: Session, portfolio_id: str) -> list[DemoAdjustment]:
    """Filas de la cartera en orden de alta (el primer evento reproducido, primero)."""
    stmt = (
        select(DemoAdjustment)
        .where(DemoAdjustment.portfolio_id == portfolio_id)
        .order_by(DemoAdjustment.id)
    )
    return list(session.scalars(stmt))


def add_demo_adjustments(session: Session, rows: Iterable[DemoAdjustment]) -> None:
    session.add_all(list(rows))
    session.flush()


def delete_demo_adjustments(
    session: Session, portfolio_id: str | None = None, event_id: str | None = None
) -> None:
    """Sin filtros, borra todos (los de todas las carteras)."""
    stmt = delete(DemoAdjustment)
    if portfolio_id is not None:
        stmt = stmt.where(DemoAdjustment.portfolio_id == portfolio_id)
    if event_id is not None:
        stmt = stmt.where(DemoAdjustment.event_id == event_id)
    session.execute(stmt)
    session.flush()


def set_plan(session: Session, portfolio_id: str, raw: dict[str, Any]) -> None:
    target = raw["target"]
    session.merge(
        Plan(
            portfolio_id=portfolio_id,
            target_equity_pct=Decimal(target["equity"]),
            target_fixed_income_pct=Decimal(target["fixed_income"]),
            target_cash_pct=Decimal(target["cash"]),
            drift_threshold=Decimal(raw["drift_threshold"]),
            goal_amount_eur=Decimal(raw["goal_amount_eur"]) if raw.get("goal_amount_eur") else None,
            goal_year=raw.get("goal_year"),
        )
    )


def add_dca_plan(session: Session, portfolio_id: str, raw: dict[str, Any]) -> None:
    session.add(
        DcaPlan(
            id=raw["id"],
            portfolio_id=portfolio_id,
            amount_eur=Decimal(raw["amount_eur"]),
            frequency=raw["frequency"],
            day=int(raw["day"]),
            status=raw["status"],
            last_execution_at=_dt(raw.get("last_execution_at")),
            next_execution_at=_dt(raw.get("next_execution_at")),
        )
    )
    session.flush()
    for allocation in raw["allocations"]:
        session.add(
            DcaAllocation(
                dca_plan_id=raw["id"],
                asset_id=allocation["asset_id"],
                weight=Decimal(allocation["weight"]),
            )
        )


def _dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None
