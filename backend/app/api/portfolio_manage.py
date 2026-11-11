"""Crear, editar, borrar e importar carteras, y preguntar sin cartera elegida (T4-09).

Crear, editar y borrar son reales desde T4-10; importar, desde T4-11 (`portfolio/importer.py`).
`/ask` es real desde T4-14 (`agents.service.ask` sin cartera elegida).
"""

from typing import Any

from fastapi import APIRouter, Response, status
from fastapi.responses import StreamingResponse

from app.agents import service as agents_service
from app.api.ask import sse as _sse
from app.portfolio import service as portfolio_service
from app.schemas.agents import AskRequest
from app.schemas.common import ErrorOut
from app.schemas.portfolio import PortfolioSummaryOut
from app.schemas.portfolio_manage import (
    PortfolioCreateRequest,
    PortfolioImportOut,
    PortfolioImportRequest,
    PortfolioUpdateRequest,
)

router = APIRouter(tags=["portfolio"])

_NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"model": ErrorOut}}
_INVALID: dict[int | str, dict[str, Any]] = {422: {"model": ErrorOut}}


@router.post(
    "/portfolios",
    response_model=PortfolioSummaryOut,
    status_code=status.HTTP_201_CREATED,
    responses=_INVALID,
)
def create_portfolio(body: PortfolioCreateRequest) -> PortfolioSummaryOut:
    """Crea una cartera vacía con id generado (`pf_` + hex). 422 si el nombre está vacío."""
    return portfolio_service.create_portfolio(body)


@router.patch(
    "/portfolios/{portfolio_id}",
    response_model=PortfolioSummaryOut,
    responses={**_NOT_FOUND, **_INVALID},
)
def update_portfolio(portfolio_id: str, body: PortfolioUpdateRequest) -> PortfolioSummaryOut:
    """Renombra la cartera o cambia su tipo o su perfil de riesgo. 404 si no existe."""
    return portfolio_service.update_portfolio(portfolio_id, body)


@router.delete(
    "/portfolios/{portfolio_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses=_NOT_FOUND,
)
def delete_portfolio(portfolio_id: str) -> Response:
    """Borra la cartera y todo lo suyo: operaciones, plan, DCA, avisos, impactos y ajustes.
    No afecta a las demás carteras. 404 si no existe."""
    portfolio_service.delete_portfolio(portfolio_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/portfolios/import",
    response_model=PortfolioImportOut,
    status_code=status.HTTP_201_CREATED,
    responses={200: {"model": PortfolioImportOut}, **_INVALID},
)
def import_portfolio(body: PortfolioImportRequest, response: Response) -> PortfolioImportOut:
    """Crea una cartera desde un CSV (formato en `PortfolioImportRequest`). Con `dry_run`, 200
    sin crear nada. Si alguna fila falla, 422 con `details.rows` (lista de `ImportRowError`)."""
    result = portfolio_service.import_portfolio(body)
    if result.dry_run:
        response.status_code = status.HTTP_200_OK
    return result


@router.post("/ask", response_class=StreamingResponse)
def ask_any_portfolio(body: AskRequest) -> StreamingResponse:
    """Como `POST /portfolios/{id}/ask`, sin cartera elegida: el asistente deduce de la pregunta
    a qué cartera o carteras se refiere y responde por separado para cada una, sin sumarlas
    (`AskSentenceEvent.portfolio_ids`). Si la pregunta es ambigua, pregunta a cuál se refiere."""
    return StreamingResponse(
        _sse(agents_service.ask(None, body)),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
