"""`GET /portfolios/{id}/alerts` (diseño del MVP §4.4)."""

from typing import Any

from fastapi import APIRouter

from app.alerts import service
from app.schemas.alerts import AlertOut
from app.schemas.common import ErrorOut

router = APIRouter(tags=["alerts"])

_NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"model": ErrorOut}}


@router.get(
    "/portfolios/{portfolio_id}/alerts", response_model=list[AlertOut], responses=_NOT_FOUND
)
def list_alerts(portfolio_id: str) -> list[AlertOut]:
    return service.list_alerts(portfolio_id)
