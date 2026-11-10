"""Crear, editar, borrar e importar carteras, y preguntar sin cartera elegida (T4-09).

Contrato: estas rutas responden con los ejemplos de `schemas/examples/` y **no guardan nada**
hasta que lleguen T4-10 (crear, editar, borrar), T4-11 (importar) y T4-14 (`/ask`).
"""

from collections.abc import Iterator
from typing import Any

from fastapi import APIRouter, Response, status
from fastapi.responses import StreamingResponse
from pydantic import TypeAdapter

from app.schemas import examples
from app.schemas.agents import (
    AskDoneEvent,
    AskEvent,
    AskMetaEvent,
    AskRequest,
    AskSentenceEvent,
)
from app.schemas.common import ErrorOut
from app.schemas.portfolio import PortfolioSummaryOut
from app.schemas.portfolio_manage import (
    LEGACY_PROFILE,
    PortfolioCreateRequest,
    PortfolioImportOut,
    PortfolioImportRequest,
    PortfolioUpdateRequest,
)

router = APIRouter(tags=["portfolio"])

_NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"model": ErrorOut}}
_INVALID: dict[int | str, dict[str, Any]] = {422: {"model": ErrorOut}}
_EVENT = TypeAdapter(AskEvent)


def _summary_example() -> PortfolioSummaryOut:
    return PortfolioSummaryOut.model_validate(examples.load("PortfolioSummaryOut"))


@router.post(
    "/portfolios",
    response_model=PortfolioSummaryOut,
    status_code=status.HTTP_201_CREATED,
    responses=_INVALID,
)
def create_portfolio(body: PortfolioCreateRequest) -> PortfolioSummaryOut:
    """Crea una cartera vacía con id generado (`pf_` + hex). 422 si el nombre está vacío."""
    return PortfolioSummaryOut(
        id="pf_3f9a2c1e7b04",
        name=body.name,
        profile=LEGACY_PROFILE[body.risk_profile],
        kind=body.kind,
        risk_profile=body.risk_profile,
    )


@router.patch(
    "/portfolios/{portfolio_id}",
    response_model=PortfolioSummaryOut,
    responses={**_NOT_FOUND, **_INVALID},
)
def update_portfolio(portfolio_id: str, body: PortfolioUpdateRequest) -> PortfolioSummaryOut:
    """Renombra la cartera o cambia su tipo o su perfil de riesgo. 404 si no existe."""
    current = _summary_example()
    changes = body.model_dump(exclude_none=True)
    if body.risk_profile is not None:
        changes["profile"] = LEGACY_PROFILE[body.risk_profile]
    return current.model_copy(update={"id": portfolio_id, **changes})


@router.delete(
    "/portfolios/{portfolio_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses=_NOT_FOUND,
)
def delete_portfolio(portfolio_id: str) -> Response:
    """Borra la cartera y todo lo suyo: operaciones, plan, DCA, avisos, impactos y ajustes.
    No afecta a las demás carteras. 404 si no existe."""
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
    result = PortfolioImportOut.model_validate(examples.load("PortfolioImportOut"))
    if body.dry_run:
        response.status_code = status.HTTP_200_OK
        return result.model_copy(update={"dry_run": True, "portfolio": None})
    portfolio = PortfolioSummaryOut(
        id="pf_3f9a2c1e7b04",
        name=body.name,
        profile=LEGACY_PROFILE[body.risk_profile],
        kind=body.kind,
        risk_profile=body.risk_profile,
    )
    return result.model_copy(update={"portfolio": portfolio})


def _example_turn() -> Iterator[str]:
    turn: list[AskEvent] = [
        AskMetaEvent.model_validate(examples.load("AskMetaEvent")),
        AskSentenceEvent.model_validate(examples.load("AskSentenceEvent")),
        AskSentenceEvent.model_validate(examples.load("AskSentenceEvent.impact")),
        AskDoneEvent.model_validate(examples.load("AskDoneEvent")),
    ]
    for event in turn:
        yield f"data: {_EVENT.dump_json(event).decode()}\n\n"


@router.post("/ask", response_class=StreamingResponse)
def ask_any_portfolio(body: AskRequest) -> StreamingResponse:
    """Como `POST /portfolios/{id}/ask`, sin cartera elegida: el asistente deduce de la pregunta
    a qué cartera o carteras se refiere y responde por separado para cada una, sin sumarlas
    (`AskSentenceEvent.portfolio_ids`). Si la pregunta es ambigua, pregunta a cuál se refiere."""
    return StreamingResponse(
        _example_turn(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
