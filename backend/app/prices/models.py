"""Tablas de precios y tipos de cambio (`SPEC.md` §6). Solo `prices/repository.py` las consulta."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
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
