"""Avisos a la cartera (`SPEC.md` §6, D-032). Solo `alerts/repository.py` los consulta."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Alert(Base):
    """`kind`: event_impact, dca_pending, drift, market_move, news_estimate. El límite semanal se
    cuenta por `created_at`. `calc_id` solo en los avisos sin evento (`market_move`,
    `news_estimate`); los de evento toman el del impacto. `news_id`: la noticia de un
    `news_estimate` (T4-31); sin clave foránea, como las noticias se cargan aparte."""

    __tablename__ = "alert"
    __table_args__ = (Index("ix_alert_portfolio_created", "portfolio_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolio.id", ondelete="CASCADE"))
    event_id: Mapped[str | None] = mapped_column(ForeignKey("event.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(16))  # AlertKind
    score: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    calc_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    news_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
