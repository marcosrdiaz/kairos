"""Endpoints de proyección y agenda (diseño del MVP §4.3, D-029)."""

from typing import Any

from fastapi import APIRouter

from app.planning import service
from app.schemas.common import ErrorOut
from app.schemas.planning import AgendaItemOut, ProjectionOut

router = APIRouter(tags=["planning"])

_NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"model": ErrorOut}}


@router.get(
    "/portfolios/{portfolio_id}/projection", response_model=ProjectionOut, responses=_NOT_FOUND
)
def get_projection(portfolio_id: str) -> ProjectionOut:
    return service.get_projection(portfolio_id)


@router.get(
    "/portfolios/{portfolio_id}/agenda", response_model=list[AgendaItemOut], responses=_NOT_FOUND
)
def get_agenda(portfolio_id: str) -> list[AgendaItemOut]:
    """T2-06 puede moverlo a `api/agenda.py`."""
    return service.get_agenda(portfolio_id)
