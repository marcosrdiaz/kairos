"""Interfaz pública de `events`: control del replay (diseño del MVP §4.6)."""

import json
from datetime import UTC, timedelta
from pathlib import Path

from app.config import get_settings
from app.core import clock
from app.core.errors import AppError, ErrorCode
from app.events import repository
from app.schemas.events import EventIn, ReplayOut, ReplayRequest

REPLAY_DIR = Path(__file__).resolve().parents[3] / "data" / "events" / "replay"
PRELOAD_EVENT_IDS = ("bce-2025-06", "oil-2025-06")
_PRELOAD_AGE = timedelta(hours=96)


def _load_replay(event_id: str) -> EventIn:
    paths = {path.stem: path for path in REPLAY_DIR.glob("*.json")}
    if event_id not in paths:
        raise AppError(ErrorCode.NOT_FOUND, "No existe ese evento.", details={"event_id": event_id})
    return EventIn.model_validate(json.loads(paths[event_id].read_text(encoding="utf-8")))


def get_event(event_id: str) -> EventIn:
    """Evento del replay. Si ya se ha inyectado, con la fecha que se le dio al inyectarlo."""
    event = _load_replay(event_id)
    occurred_at = repository.get_occurred_at(event_id)
    if occurred_at is None:
        return event
    # SQLite devuelve la fecha sin zona; en BD siempre es UTC.
    utc = occurred_at if occurred_at.tzinfo else occurred_at.replace(tzinfo=UTC)
    return event.model_copy(update={"occurred_at": utc})


def replay(event_id: str, request: ReplayRequest | None = None) -> ReplayOut:
    """Inyecta un evento del modo replay. Solo con `DEMO_MODE=true`."""
    if not get_settings().demo_mode:
        raise AppError(ErrorCode.DEMO_MODE_DISABLED, "El modo demo está desactivado.")
    from app.events import pipeline  # aquí para evitar el ciclo events → impact → events

    options = request or ReplayRequest()
    return pipeline.run(_load_replay(event_id), options.occurred_at, options.silent)


def preload() -> list[str]:
    """Precarga del guion: BCE y petróleo, fuera de las 72 h de Atento y sin gastar avisos."""
    occurred_at = clock.now() - _PRELOAD_AGE
    request = ReplayRequest(occurred_at=occurred_at, silent=True)
    for event_id in PRELOAD_EVENT_IDS:
        replay(event_id, request)
    return list(PRELOAD_EVENT_IDS)


def reset() -> None:
    """Borra los eventos. Antes hay que llamar a `impact.service.reset`."""
    repository.delete_all()
