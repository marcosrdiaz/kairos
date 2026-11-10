"""Tablas del gestor de cartera (`SPEC.md` §6). Solo `portfolio/repository.py` las consulta.

No hay tabla `position`: las posiciones se derivan de `tax_lot`. El libro (`transaction`) es la
fuente de verdad. Los enums se guardan como texto con los valores de `app.schemas`.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

# Tipos de columna (CLAUDE.md: euros NUMERIC(18,2); participaciones y precios NUMERIC(20,8)).
EUR = Numeric(18, 2)
UNITS = Numeric(20, 8)
PRICE = Numeric(20, 8)
FRACTION = Numeric(10, 8)
TZ = DateTime(timezone=True)


class Portfolio(Base):
    __tablename__ = "portfolio"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    profile: Mapped[str] = mapped_column(String(16))  # Profile (obsoleto, sale de risk_profile)
    kind: Mapped[str | None] = mapped_column(String(16))  # PortfolioKind (T4-10)
    risk_profile: Mapped[str | None] = mapped_column(String(16))  # RiskProfile (T4-10)
    base_currency: Mapped[str] = mapped_column(String(3), default="EUR")
    created_at: Mapped[datetime] = mapped_column(TZ)


class Plan(Base):
    __tablename__ = "plan"

    portfolio_id: Mapped[str] = mapped_column(
        ForeignKey("portfolio.id", ondelete="CASCADE"), primary_key=True
    )
    target_equity_pct: Mapped[Decimal] = mapped_column(FRACTION)
    target_fixed_income_pct: Mapped[Decimal] = mapped_column(FRACTION)
    target_cash_pct: Mapped[Decimal] = mapped_column(FRACTION)
    drift_threshold: Mapped[Decimal] = mapped_column(FRACTION, default=Decimal("0.10"))
    goal_amount_eur: Mapped[Decimal | None] = mapped_column(EUR)
    goal_year: Mapped[int | None] = mapped_column(Integer)


class Asset(Base):
    """`id` es el ISIN; sin ISIN, un código propio (`DEP-12M`, `PP-MIXTO`, D-038)."""

    __tablename__ = "asset"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    isin: Mapped[str | None] = mapped_column(String(12), unique=True)
    ticker: Mapped[str | None] = mapped_column(String(20), index=True)
    name: Mapped[str] = mapped_column(String(200))
    asset_type: Mapped[str] = mapped_column(String(16))  # AssetType
    asset_class: Mapped[str] = mapped_column(String(16))  # AssetClass
    currency: Mapped[str] = mapped_column(String(3))
    ter: Mapped[Decimal | None] = mapped_column(FRACTION)
    transferable: Mapped[bool] = mapped_column(Boolean, default=False)
    price_kind: Mapped[str] = mapped_column(String(16))  # PriceKind
    price_source: Mapped[str] = mapped_column(String(80))  # `yahoo:<símbolo>` o `fixed:<valor>`


class Transaction(Base):
    """Libro de operaciones. `type`: buy, sell, transfer_out, transfer_in, dca_buy, initial."""

    __tablename__ = "transaction"
    __table_args__ = (Index("ix_transaction_portfolio_ts", "portfolio_id", "ts"),)

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolio.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(16))
    asset_id: Mapped[str] = mapped_column(ForeignKey("asset.id"))
    ts: Mapped[datetime] = mapped_column(TZ)
    units: Mapped[Decimal] = mapped_column(UNITS)
    price: Mapped[Decimal] = mapped_column(PRICE)
    price_currency: Mapped[str] = mapped_column(String(3))
    fx_rate: Mapped[Decimal] = mapped_column(PRICE, default=Decimal("1"))
    amount_eur: Mapped[Decimal] = mapped_column(EUR)
    realized_gain_eur: Mapped[Decimal | None] = mapped_column(EUR)
    linked_tx_id: Mapped[str | None] = mapped_column(ForeignKey("transaction.id"))
    dca_plan_id: Mapped[str | None] = mapped_column(ForeignKey("dca_plan.id"))
    calc_id: Mapped[str | None] = mapped_column(String(40))


class TaxLot(Base):
    """Lote fiscal. Base de FIFO y de los traspasos (que conservan `acquired_at` y coste)."""

    __tablename__ = "tax_lot"
    __table_args__ = (Index("ix_tax_lot_fifo", "portfolio_id", "asset_id", "acquired_at"),)

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolio.id", ondelete="CASCADE"))
    asset_id: Mapped[str] = mapped_column(ForeignKey("asset.id"))
    acquired_at: Mapped[datetime] = mapped_column(TZ)
    units_initial: Mapped[Decimal] = mapped_column(UNITS)
    units_remaining: Mapped[Decimal] = mapped_column(UNITS)
    cost_eur_per_unit: Mapped[Decimal] = mapped_column(PRICE)
    origin_tx_id: Mapped[str | None] = mapped_column(ForeignKey("transaction.id"))


class DcaPlan(Base):
    __tablename__ = "dca_plan"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    portfolio_id: Mapped[str] = mapped_column(
        ForeignKey("portfolio.id", ondelete="CASCADE"), index=True
    )
    amount_eur: Mapped[Decimal] = mapped_column(EUR)
    frequency: Mapped[str] = mapped_column(String(16))  # Frequency
    day: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16))  # DcaPlanStatus
    last_execution_at: Mapped[datetime | None] = mapped_column(TZ)
    next_execution_at: Mapped[datetime | None] = mapped_column(TZ)


class DcaAllocation(Base):
    """Reparto del plan. Σ weight = 1 (lo valida el servicio)."""

    __tablename__ = "dca_allocation"

    dca_plan_id: Mapped[str] = mapped_column(
        ForeignKey("dca_plan.id", ondelete="CASCADE"), primary_key=True
    )
    asset_id: Mapped[str] = mapped_column(ForeignKey("asset.id"), primary_key=True)
    weight: Mapped[Decimal] = mapped_column(FRACTION)


class DcaExecution(Base):
    """Ejecución de un plan DCA: `pending` hasta que el usuario confirma o salta."""

    __tablename__ = "dca_execution"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    dca_plan_id: Mapped[str] = mapped_column(
        ForeignKey("dca_plan.id", ondelete="CASCADE"), index=True
    )
    scheduled_for: Mapped[datetime] = mapped_column(TZ)
    status: Mapped[str] = mapped_column(String(16))  # DcaExecutionStatus
    created_at: Mapped[datetime] = mapped_column(TZ)
    resolved_at: Mapped[datetime | None] = mapped_column(TZ)


class DcaExecutionLine(Base):
    """Línea de una ejecución, con el precio usado para estimar participaciones."""

    __tablename__ = "dca_execution_line"

    execution_id: Mapped[str] = mapped_column(
        ForeignKey("dca_execution.id", ondelete="CASCADE"), primary_key=True
    )
    asset_id: Mapped[str] = mapped_column(ForeignKey("asset.id"), primary_key=True)
    amount_eur: Mapped[Decimal] = mapped_column(EUR)
    price: Mapped[Decimal] = mapped_column(PRICE)
    price_at: Mapped[datetime] = mapped_column(TZ)
    units_estimated: Mapped[Decimal] = mapped_column(UNITS)
    transaction_id: Mapped[str | None] = mapped_column(ForeignKey("transaction.id"))


class DemoAdjustment(Base):
    """Ajuste de demo por posición tras un replay (D-031). Solo con `DEMO_MODE=true`.

    Los precios no se tocan; la valoración suma estos importes. `/demo/reset` vacía la tabla.
    """

    __tablename__ = "demo_adjustment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    portfolio_id: Mapped[str] = mapped_column(
        ForeignKey("portfolio.id", ondelete="CASCADE"), index=True
    )
    event_id: Mapped[str] = mapped_column(ForeignKey("event.id", ondelete="CASCADE"))
    asset_id: Mapped[str] = mapped_column(ForeignKey("asset.id"))
    impact_eur: Mapped[Decimal] = mapped_column(EUR)
    label: Mapped[str] = mapped_column(String(80))
    calc_id: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(TZ)


__all__ = [
    "Asset",
    "DcaAllocation",
    "DcaExecution",
    "DcaExecutionLine",
    "DcaPlan",
    "DemoAdjustment",
    "Plan",
    "Portfolio",
    "TaxLot",
    "Transaction",
]
