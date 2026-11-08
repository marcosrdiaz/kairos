"""Control de replay: `POST /demo/replay/{event_id}` (diseño del MVP §4.6).

`GET /portfolios/{id}/events` es de impacto (`api/impact.py`, T0-04), no de este módulo.
"""

from typing import Any

from fastapi import APIRouter

from app.events import service
from app.schemas.common import ErrorOut
from app.schemas.events import ReplayOut

router = APIRouter(tags=["events"])

_ERRORS: dict[int | str, dict[str, Any]] = {403: {"model": ErrorOut}, 404: {"model": ErrorOut}}


@router.post("/demo/replay/{event_id}", response_model=ReplayOut, responses=_ERRORS)
def replay_event(event_id: str) -> ReplayOut:
    return service.replay(event_id)
