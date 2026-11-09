"""Endpoint de exposición (diseño del MVP §4.3). El radar está en `api/radar.py`."""

from typing import Any

from fastapi import APIRouter

from app.exposure import service
from app.schemas.common import ErrorOut
from app.schemas.exposure import ExposureOut

router = APIRouter(tags=["exposure"])

_NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"model": ErrorOut}}


@router.get("/portfolios/{portfolio_id}/exposure", response_model=ExposureOut, responses=_NOT_FOUND)
def get_exposure(portfolio_id: str) -> ExposureOut:
    return service.get_exposure(portfolio_id)
