"""Ticker de mercado de Inicio (T2-17): último precio y variación de los activos de la cartera.

Solo contrato por ahora: la implementación llega en el PR de T2-17 y, mientras, la ruta responde
`UPSTREAM_UNAVAILABLE`.
"""

from typing import Any

from fastapi import APIRouter

from app.core.errors import AppError, ErrorCode
from app.schemas.common import ErrorOut
from app.schemas.prices import TickerOut

router = APIRouter(tags=["prices"])

_ERRORS: dict[int | str, dict[str, Any]] = {404: {"model": ErrorOut}, 503: {"model": ErrorOut}}


@router.get("/portfolios/{portfolio_id}/ticker", response_model=TickerOut, responses=_ERRORS)
def get_ticker(portfolio_id: str) -> TickerOut:
    """Último precio de cada posición y su variación frente al cierre anterior."""
    raise AppError(
        ErrorCode.UPSTREAM_UNAVAILABLE,
        "El ticker de mercado todavía no está disponible.",
        details={"portfolio_id": portfolio_id},
    )
