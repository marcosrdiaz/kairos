"""Control de replay: `POST /demo/replay/{event_id}` (diseño del MVP §4.6), y eventos pendientes
de cierre: `GET /events/pending` (T4-04).

`GET /portfolios/{id}/events` es de impacto (`api/impact.py`, T0-04), no de este módulo.
"""

from typing import Any

from fastapi import APIRouter

from app.events import service
from app.schemas import examples
from app.schemas.common import ErrorOut
from app.schemas.events import PendingEventOut, ReplayOut, ReplayRequest

router = APIRouter(tags=["events"])

_ERRORS: dict[int | str, dict[str, Any]] = {403: {"model": ErrorOut}, 404: {"model": ErrorOut}}


@router.post("/demo/replay/{event_id}", response_model=ReplayOut, responses=_ERRORS)
def replay_event(event_id: str, body: ReplayRequest | None = None) -> ReplayOut:
    return service.replay(event_id, body)


@router.get("/events/pending", response_model=list[PendingEventOut])
def list_pending_events() -> list[PendingEventOut]:
    """Eventos reales pendientes de cierre (T4-04, D-089): noticia y cadena causal, sin cifras.
    Iguales para todas las carteras; el más antiguo primero. Lista vacía si no hay ninguno."""
    # Contrato: sirve el ejemplo hasta la implementación (T4-04, parte 2).
    return [PendingEventOut.model_validate(examples.load("PendingEventOut"))]
