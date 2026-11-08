"""Acceso a la tabla `event`. Solo aquí se consulta."""

from datetime import datetime

from sqlalchemy import delete, select

from app.core.db import session_scope
from app.events.models import Event
from app.schemas.events import EventAnalysis, EventIn


def save_event(
    event: EventIn, occurred_at: datetime, analysis: EventAnalysis, created_at: datetime
) -> None:
    """Guarda el evento con su análisis. Si se reinyecta, sustituye el anterior."""
    with session_scope() as session:
        session.merge(
            Event(
                id=event.id,
                type=event.type.value,
                title=event.title,
                text=event.text,
                occurred_at=occurred_at,
                replay=True,
                source_urls=event.source_urls,
                entities=[entity.model_dump(mode="json") for entity in analysis.entities],
                analysis=analysis.model_dump(mode="json"),
                analyzed_model=analysis.analyzed_model,
                created_at=created_at,
            )
        )


def get_occurred_at(event_id: str) -> datetime | None:
    with session_scope() as session:
        return session.scalar(select(Event.occurred_at).where(Event.id == event_id))


def delete_all() -> None:
    with session_scope() as session:
        session.execute(delete(Event))
