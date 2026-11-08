"""Composición de fondos y ETF para el look-through (`SPEC.md` §6).

Solo `exposure/repository.py` la consulta. Pesos normalizados; "Otros" agrupa el resto.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Composition(Base):
    __tablename__ = "composition"

    fund_asset_id: Mapped[str] = mapped_column(
        ForeignKey("asset.id", ondelete="CASCADE"), primary_key=True
    )
    constituent_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    weight: Mapped[Decimal] = mapped_column(Numeric(10, 8))
    country: Mapped[str | None] = mapped_column(String(64))
    sector: Mapped[str | None] = mapped_column(String(64))
    currency: Mapped[str | None] = mapped_column(String(3))
    as_of: Mapped[date] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String(300))
