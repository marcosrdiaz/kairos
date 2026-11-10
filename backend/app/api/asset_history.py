"""Evolución de una posición (T2-23): `GET /portfolios/{id}/positions/{asset_id}/history?period=`.

Contrato: sirve el ejemplo de `schemas/examples/` hasta que llegue el cálculo real (T2-23).
"""

from typing import Any

from fastapi import APIRouter

from app.schemas import examples
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
    example = AssetHistoryOut.model_validate(examples.load("AssetHistoryOut"))
    return example.model_copy(
        update={"portfolio_id": portfolio_id, "asset_id": asset_id, "period": period}
    )
