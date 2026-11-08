"""Tablas del motor de impacto (`SPEC.md` §6). Solo `impact/repository.py` las consulta."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

EUR = Numeric(18, 2)
STAT = Numeric(20, 8)


class FactorBeta(Base):
    """Sensibilidad de un activo a un factor. La calcula `make betas` (T1-12)."""

    __tablename__ = "factor_beta"

    asset_id: Mapped[str] = mapped_column(
        ForeignKey("asset.id", ondelete="CASCADE"), primary_key=True
    )
    factor: Mapped[str] = mapped_column(String(16), primary_key=True)  # Factor
    beta: Mapped[Decimal] = mapped_column(STAT)
    std_err: Mapped[Decimal] = mapped_column(STAT)
    r2: Mapped[Decimal] = mapped_column(STAT)
    n_obs: Mapped[int] = mapped_column(Integer)
    window_start: Mapped[date] = mapped_column(Date)
    window_end: Mapped[date] = mapped_column(Date)


class EventImpact(Base):
    """Impacto estimado de un evento sobre una cartera (rango, no cifra exacta)."""

    __tablename__ = "event_impact"

    event_id: Mapped[str] = mapped_column(
        ForeignKey("event.id", ondelete="CASCADE"), primary_key=True
    )
    portfolio_id: Mapped[str] = mapped_column(
        ForeignKey("portfolio.id", ondelete="CASCADE"), primary_key=True
    )
    impact_eur: Mapped[Decimal] = mapped_column(EUR)
    low_eur: Mapped[Decimal] = mapped_column(EUR)
    high_eur: Mapped[Decimal] = mapped_column(EUR)
    impact_pct: Mapped[Decimal] = mapped_column(STAT)
    confidence: Mapped[str] = mapped_column(String(8))  # Confidence
    polarity: Mapped[str] = mapped_column(String(16))  # Polarity
    breakdown: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    explanation: Mapped[str | None] = mapped_column(Text)
    explanation_status: Mapped[str] = mapped_column(String(16), default="pending")
    calc_id: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
