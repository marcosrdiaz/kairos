"""Acceso a la tabla `event`. Solo aquí se consulta."""

from datetime import datetime

from sqlalchemy import delete, select

from app.core.db import session_scope
from app.events.models import Event, PendingEvent
from app.schemas.events import EventAnalysis, EventIn


def save_event(
    event: EventIn,
    occurred_at: datetime,
    analysis: EventAnalysis,
    created_at: datetime,
    replay: bool = True,
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
                replay=replay,
                source_urls=event.source_urls,
                entities=[entity.model_dump(mode="json") for entity in analysis.entities],
                analysis=analysis.model_dump(mode="json"),
                analyzed_model=analysis.analyzed_model,
                created_at=created_at,
                payload=None if replay else event.model_dump(mode="json"),
            )
        )


def get_payload(event_id: str) -> EventIn | None:
    """`EventIn` de un evento real guardado; `None` si no existe o es del replay."""
    with session_scope() as session:
        raw = session.scalar(select(Event.payload).where(Event.id == event_id))
    return EventIn.model_validate(raw) if raw is not None else None


def get_occurred_at(event_id: str) -> datetime | None:
    with session_scope() as session:
        return session.scalar(select(Event.occurred_at).where(Event.id == event_id))


def get_analysis(event_id: str) -> EventAnalysis | None:
    with session_scope() as session:
        raw = session.scalar(select(Event.analysis).where(Event.id == event_id))
    return EventAnalysis.model_validate(raw) if raw is not None else None


def delete_all() -> None:
    with session_scope() as session:
        session.execute(delete(PendingEvent))
        session.execute(delete(Event))


# --- Pendientes de cierre (T4-04) ---


def save_pending(event: EventIn, companies: dict[str, str], created_at: datetime) -> None:
    with session_scope() as session:
        session.merge(
            PendingEvent(
                id=event.id,
                payload=event.model_dump(mode="json"),
                companies=dict(companies),
                created_at=created_at,
            )
        )


def list_pending() -> list[tuple[EventIn, dict[str, str]]]:
    """Por orden de alta: el más antiguo primero."""
    with session_scope() as session:
        rows = session.scalars(select(PendingEvent).order_by(PendingEvent.created_at))
        return [(EventIn.model_validate(r.payload), dict(r.companies)) for r in rows]


def delete_pending(event_id: str) -> None:
    with session_scope() as session:
        session.execute(delete(PendingEvent).where(PendingEvent.id == event_id))
