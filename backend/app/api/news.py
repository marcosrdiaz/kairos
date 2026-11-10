"""Noticias de una cartera (T4-27): `GET /portfolios/{id}/news` y `.../news/{news_id}`.

Rutas provisionales: responden con los ejemplos de `schemas/examples/NewsItemOut*.json` (marcados
`illustrative`) hasta que la ingesta (T4-28) y la estimación (T4-30) las sirvan con datos reales.
La cartera sí se comprueba: 404 si no existe.
"""

from typing import Any

from fastapi import APIRouter, Query

from app.core.errors import AppError, ErrorCode
from app.portfolio import service as portfolio_service
from app.schemas import examples
from app.schemas.common import ErrorOut
from app.schemas.news import NewsCategory, NewsEstimateStatus, NewsItemOut

router = APIRouter(tags=["news"])

_NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"model": ErrorOut}}
_EXAMPLES = ("NewsItemOut", "NewsItemOut.pending", "NewsItemOut.not_relevant")


def _example_items() -> list[NewsItemOut]:
    items = [NewsItemOut.model_validate(examples.load(name)) for name in _EXAMPLES]
    return sorted(items, key=lambda item: item.published_at, reverse=True)


def _affects(item: NewsItemOut) -> bool:
    return item.estimate is None or item.estimate.status != NewsEstimateStatus.NOT_RELEVANT


@router.get(
    "/portfolios/{portfolio_id}/news", response_model=list[NewsItemOut], responses=_NOT_FOUND
)
def list_news(
    portfolio_id: str,
    category: NewsCategory | None = None,
    affecting: bool = True,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[NewsItemOut]:
    """Noticias de la más reciente a la más antigua, con su impacto estimado en esta cartera.

    `affecting=true` (por defecto) deja fuera las `not_relevant`; `category` filtra por tipo.
    404 si la cartera no existe."""
    portfolio_service.ensure_exists(portfolio_id)
    items = [
        item
        for item in _example_items()
        if (category is None or item.category == category) and (not affecting or _affects(item))
    ]
    return items[:limit]


@router.get(
    "/portfolios/{portfolio_id}/news/{news_id}",
    response_model=NewsItemOut,
    responses=_NOT_FOUND,
)
def get_news(portfolio_id: str, news_id: str) -> NewsItemOut:
    """Una noticia con su impacto estimado en esta cartera. 404 si no existe la cartera o la
    noticia."""
    portfolio_service.ensure_exists(portfolio_id)
    for item in _example_items():
        if item.id == news_id:
            return item
    raise AppError(ErrorCode.NOT_FOUND, "No encontramos esa noticia.", {"news_id": news_id})
