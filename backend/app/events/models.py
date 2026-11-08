"""Eventos financieros, reales o de replay (`SPEC.md` §6).

Solo `events/repository.py` los consulta.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Event(Base):
    """`analysis` guarda el `EventAnalysis` del analizador como JSON."""

    __tablename__ = "event"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    type: Mapped[str] = mapped_column(String(16))  # EventType
    title: Mapped[str] = mapped_column(String(300))
    text: Mapped[str] = mapped_column(Text, default="")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    replay: Mapped[bool] = mapped_column(Boolean, default=False)
    source_urls: Mapped[list[str]] = mapped_column(JSON)
    entities: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    analysis: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    analyzed_model: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
