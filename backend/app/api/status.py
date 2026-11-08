"""Endpoint del estado de la cartera para el widget (diseño del MVP §4.3)."""

from typing import Any

from fastapi import APIRouter

from app.schemas.common import ErrorOut
from app.schemas.status import StatusOut
from app.status import service

router = APIRouter(tags=["status"])

_NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"model": ErrorOut}}


@router.get("/portfolios/{portfolio_id}/status", response_model=StatusOut, responses=_NOT_FOUND)
def get_status(portfolio_id: str) -> StatusOut:
    return service.get_status(portfolio_id)
