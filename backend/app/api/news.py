"""Noticias de una cartera: `GET /portfolios/{id}/news` y `.../news/{news_id}` (T4-27, T4-30).

Noticias reales (T4-28) clasificadas por Claude (T4-29) con su impacto en la cartera calculado
por el motor (T4-30). Sin datos de ejemplo.
"""

from typing import Any

from fastapi import APIRouter, Query

from app.news import service as news_service
from app.schemas.common import ErrorOut
from app.schemas.news import NewsCategory, NewsItemOut

router = APIRouter(tags=["news"])

_NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"model": ErrorOut}}


@router.get(
    "/portfolios/{portfolio_id}/news", response_model=list[NewsItemOut], responses=_NOT_FOUND
)
def list_news(
    portfolio_id: str,
    category: NewsCategory | None = None,
    affecting: bool = True,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[NewsItemOut]:
    """Noticias de la más reciente a la más antigua, con su impacto en esta cartera.

    `affecting=true` (por defecto): solo las que mueven alguna posición; `category` filtra por
    tipo. 404 si la cartera no existe."""
    return news_service.list_for_portfolio(portfolio_id, category, affecting, limit)


@router.get(
    "/portfolios/{portfolio_id}/news/{news_id}",
    response_model=NewsItemOut,
    responses=_NOT_FOUND,
)
def get_news(portfolio_id: str, news_id: str) -> NewsItemOut:
    """Una noticia con su impacto en esta cartera. 404 si no existe la cartera o la noticia."""
    return news_service.get_for_portfolio(portfolio_id, news_id)
