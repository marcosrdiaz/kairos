"""Noticias de una cartera (T4-27): `GET /portfolios/{id}/news` y `.../news/{news_id}`.

Rutas provisionales del contrato: **no sirven datos de ejemplo**. Hasta que la ingesta (T4-28) y
la estimación (T4-30) estén, la lista sale vacía y el detalle da 404. Los ejemplos de
`schemas/examples/NewsItemOut*.json` son solo mocks del frontend y de los tests.
"""

from typing import Any

from fastapi import APIRouter, Query

from app.core.errors import AppError, ErrorCode
from app.portfolio import service as portfolio_service
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

    `affecting=true` (por defecto) deja fuera las `not_relevant`; `category` filtra por tipo.
    404 si la cartera no existe."""
    portfolio_service.ensure_exists(portfolio_id)
    return []


@router.get(
    "/portfolios/{portfolio_id}/news/{news_id}",
    response_model=NewsItemOut,
    responses=_NOT_FOUND,
)
def get_news(portfolio_id: str, news_id: str) -> NewsItemOut:
    """Una noticia con su impacto en esta cartera. 404 si no existe la cartera o la noticia."""
    portfolio_service.ensure_exists(portfolio_id)
    raise AppError(ErrorCode.NOT_FOUND, "No encontramos esa noticia.", {"news_id": news_id})
