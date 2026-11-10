"""Ticker de mercado de Inicio (T2-17): último precio y variación de los activos de la cartera.

Las posiciones salen de `portfolio.service` y los precios, la variación y la traza de
`prices.service`; aquí solo se juntan.
"""

from typing import Any

from fastapi import APIRouter

from app.core import clock
from app.portfolio import service as portfolio_service
from app.prices import service as prices_service
from app.schemas.common import ErrorOut
from app.schemas.prices import TickerOut

router = APIRouter(tags=["prices"])

_ERRORS: dict[int | str, dict[str, Any]] = {404: {"model": ErrorOut}, 503: {"model": ErrorOut}}


@router.get("/portfolios/{portfolio_id}/ticker", response_model=TickerOut, responses=_ERRORS)
def get_ticker(portfolio_id: str) -> TickerOut:
    """Último precio de cada posición y su variación frente al cierre anterior."""
    positions = portfolio_service.get_valued(portfolio_id).positions
    items = [prices_service.ticker_item(p.asset_id, p.ticker, p.name) for p in positions]
    return TickerOut(portfolio_id=portfolio_id, as_of=clock.now(), items=items)
