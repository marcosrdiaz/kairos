"""Mock de eventos: sirve el ejemplo de `ReplayOut` (D-018) y los JSON del modo replay.

Lo sustituye T1-15; se borra en T2-03.
"""

import json
from pathlib import Path

from app.core.errors import AppError, ErrorCode
from app.schemas import examples
from app.schemas.events import EventIn, ReplayOut

REPLAY_DIR = Path(__file__).resolve().parents[3] / "data" / "events" / "replay"


def replay(event_id: str) -> ReplayOut:
    result = ReplayOut.model_validate(examples.load("ReplayOut"))
    return result.model_copy(update={"event_id": event_id})


def get_event(event_id: str) -> EventIn:
    paths = {path.stem: path for path in REPLAY_DIR.glob("*.json")}
    if event_id not in paths:
        raise AppError(ErrorCode.NOT_FOUND, "No existe ese evento.", details={"event_id": event_id})
    return EventIn.model_validate(json.loads(paths[event_id].read_text(encoding="utf-8")))
