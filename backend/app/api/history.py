"""Evolución del valor de la cartera (T2-18): `GET /portfolios/{id}/history?period=`.

Contrato: sirve el ejemplo de `schemas/examples/` hasta que llegue el cálculo real (T2-18).
"""

from typing import Any

from fastapi import APIRouter

from app.schemas import examples
from app.schemas.common import ErrorOut
from app.schemas.history import HistoryPeriod, PortfolioHistoryOut

router = APIRouter(tags=["portfolio"])

_ERRORS: dict[int | str, dict[str, Any]] = {404: {"model": ErrorOut}, 503: {"model": ErrorOut}}


@router.get(
    "/portfolios/{portfolio_id}/history", response_model=PortfolioHistoryOut, responses=_ERRORS
)
def get_history(
    portfolio_id: str, period: HistoryPeriod = HistoryPeriod.ONE_YEAR
) -> PortfolioHistoryOut:
    """Valor de la cartera con precios de cierre, sin ajustes de demo. 404 si no existe la
    cartera; 503 (`PRICE_UNAVAILABLE`) si no hay ningún precio en el periodo."""
    example = PortfolioHistoryOut.model_validate(examples.load("PortfolioHistoryOut"))
    return example.model_copy(update={"portfolio_id": portfolio_id, "period": period})
