"""Endpoint del radar de riesgos y oportunidades (diseño del MVP §4.3)."""

from typing import Any

from fastapi import APIRouter

from app.exposure import service
from app.schemas.common import ErrorOut
from app.schemas.radar import RadarOut

router = APIRouter(tags=["exposure"])

_NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"model": ErrorOut}}


@router.get("/portfolios/{portfolio_id}/radar", response_model=RadarOut, responses=_NOT_FOUND)
def get_radar(portfolio_id: str) -> RadarOut:
    return service.get_radar(portfolio_id)
