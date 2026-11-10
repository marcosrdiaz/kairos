"""Evolución de una posición (T2-23): `GET /portfolios/{id}/positions/{asset_id}/history?period=`.

Mismas reglas que la serie de la cartera (`portfolio/history.py`) con las operaciones de ese activo.
"""

from typing import Any

from fastapi import APIRouter

from app.portfolio import asset_history
from app.schemas.common import ErrorOut
from app.schemas.history import AssetHistoryOut, HistoryPeriod

router = APIRouter(tags=["portfolio"])

_ERRORS: dict[int | str, dict[str, Any]] = {404: {"model": ErrorOut}, 503: {"model": ErrorOut}}


@router.get(
    "/portfolios/{portfolio_id}/positions/{asset_id}/history",
    response_model=AssetHistoryOut,
    responses=_ERRORS,
)
def get_asset_history(
    portfolio_id: str, asset_id: str, period: HistoryPeriod = HistoryPeriod.ONE_YEAR
) -> AssetHistoryOut:
    """Valor de una posición con precios de cierre, sin ajustes de demo. 404 si no existe la
    cartera o nunca tuvo el activo; 503 (`PRICE_UNAVAILABLE`) si no hay ningún precio en el
    periodo."""
    return asset_history.get_asset_history(portfolio_id, asset_id, period)
