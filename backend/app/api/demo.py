"""Control de demo: `POST /demo/reset` y `/demo/dca/run` (diseño del MVP §4.6). Solo con
`DEMO_MODE=true`.

`/demo/replay` vive en `api/events.py`. `PUT /demo/clock` (T2-03) se añade aquí.
"""

from typing import Any

from fastapi import APIRouter

from app.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.events import service as events_service
from app.impact import service as impact_service
from app.portfolio import service as portfolio_service
from app.schemas.common import ErrorOut
from app.schemas.demo import DemoResetOut, DemoResetRequest
from app.schemas.portfolio import DcaExecutionOut
from app.status import service as status_service

router = APIRouter(tags=["demo"])

_FORBIDDEN: dict[int | str, dict[str, Any]] = {403: {"model": ErrorOut}}


def _require_demo_mode() -> None:
    if not get_settings().demo_mode:
        raise AppError(ErrorCode.DEMO_MODE_DISABLED, "El modo demo está desactivado.")


@router.post("/demo/reset", response_model=DemoResetOut, responses=_FORBIDDEN)
def reset_demo(body: DemoResetRequest | None = None) -> DemoResetOut:
    """Recarga Laura y Javier y borra eventos e impactos. `preload` reproduce BCE y petróleo."""
    _require_demo_mode()
    portfolio_ids = portfolio_service.reset_demo()
    impact_service.reset()
    status_service.reset()
    events_service.reset()
    preloaded = events_service.preload() if body is not None and body.preload else []
    return DemoResetOut(portfolio_ids=portfolio_ids, preloaded_event_ids=preloaded)


@router.post("/demo/dca/run", response_model=list[DcaExecutionOut], responses=_FORBIDDEN)
def run_dca() -> list[DcaExecutionOut]:
    """Crea las aportaciones pendientes de hoy de los planes DCA activos y las devuelve."""
    _require_demo_mode()
    return portfolio_service.run_dca_demo()
