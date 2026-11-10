"""Eventos financieros, reales o de replay (`SPEC.md` §6).

Solo `events/repository.py` los consulta.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text
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
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    """`EventIn` completo de un evento real (T4-04); `null` en los del replay, que viven en
    `data/events/replay`."""


class AnalysisCache(Base):
    """Análisis del modelo ya hechos (T2-26, D-083), para no volver a llamarlo al repetir un evento.

    `key` = versión del prompt + huella de la entrada (`agents.analysis_cache_key`): si cambia el
    prompt o el evento, la fila ya no se usa. A diferencia de `event`, `/demo/reset` no la borra:
    así el guion no llama al modelo en cada ensayo. Solo guarda análisis del modelo, no respaldos.
    """

    __tablename__ = "analysis_cache"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    key: Mapped[str] = mapped_column(String(40), primary_key=True)
    analysis: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PendingEvent(Base):
    """Evento pendiente de cierre (T4-04, D-089): aún no se puede medir su shock. Guarda el
    `EventIn` completo y las empresas que hay que medir (`clave → asset_id`) para procesarlo
    tras el cierre. Su fila de `event` (con la cadena causal) ya existe; sus impactos, no."""

    __tablename__ = "pending_event"

    id: Mapped[str] = mapped_column(
        String(64), ForeignKey("event.id", ondelete="CASCADE"), primary_key=True
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    companies: Mapped[dict[str, str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
