"""Tablas de precios y tipos de cambio (`SPEC.md` §6). Solo `prices/repository.py` las consulta."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Price(Base):
    __tablename__ = "price"

    asset_id: Mapped[str] = mapped_column(
        ForeignKey("asset.id", ondelete="CASCADE"), primary_key=True
    )
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    value: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    currency: Mapped[str] = mapped_column(String(3))
    source: Mapped[str] = mapped_column(String(80))


class FxRate(Base):
    """`pair` como `EURUSD`: unidades de la segunda divisa por una de la primera."""

    __tablename__ = "fx_rate"

    pair: Mapped[str] = mapped_column(String(6), primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    rate: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    source: Mapped[str] = mapped_column(String(80))


class FactorClose(Base):
    """Cierre diario de un factor (`Factor`, T4-01). `RATES_EUR` es una rentabilidad en fracción
    (puede ser negativa); por eso 12 decimales. `source` dice de dónde salió (`yahoo:^NDX`,
    `ecb:…`) y `fetched_at`, cuándo se pidió."""

    __tablename__ = "factor_close"

    factor: Mapped[str] = mapped_column(String(16), primary_key=True)
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    value: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    source: Mapped[str] = mapped_column(String(80))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
