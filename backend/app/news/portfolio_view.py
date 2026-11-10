"""Noticias vistas desde una cartera (T4-30): `NewsItemOut` con su impacto en esa cartera.

La clasificación (T4-29) da categoría, empresas, canales, cadena causal y relevancia; el motor de
impacto (`impact.service.estimate_news_impacts`) pone todas las cifras. Cada cartera por separado:
nunca se suman cifras entre carteras.
"""

from datetime import timedelta

from app.core import clock
from app.impact import service as impact_service
from app.news import repository
from app.news.ingest import topics
from app.news.models import NewsItem
from app.news.repository import as_utc
from app.schemas.common import SourceKind, SourceRef
from app.schemas.events import CompanyRef, Relevance
from app.schemas.news import (
    NewsCategory,
    NewsChannel,
    NewsEstimateOut,
    NewsEstimateStatus,
    NewsItemOut,
)

WINDOW = timedelta(days=45)
"""Solo se calculan las noticias de este periodo hasta el reloj."""

_SHOWN = (NewsEstimateStatus.ESTIMATED, NewsEstimateStatus.MEASURED)


def _company_assets() -> dict[str, str]:
    return {c.key: c.asset_id for c in topics.COMPANIES if c.asset_id}


def _is_relevant(row: NewsItem) -> bool:
    c = row.classification
    return c is not None and c["relevance"] != Relevance.LOW.value and bool(c["channels"])


def _out(row: NewsItem, estimate: NewsEstimateOut | None, asset_ids: list[str]) -> NewsItemOut:
    c = row.classification or {}
    published = as_utc(row.published_at)
    return NewsItemOut(
        id=row.id,
        category=NewsCategory(c.get("category", NewsCategory.OTHER.value)),
        title=row.title,
        summary=c.get("summary_es") or row.summary or row.title,
        published_at=published,
        source=SourceRef(
            kind=SourceKind.EVENT, label=row.source_name, ref=row.id, as_of=published, url=row.url
        ),
        companies=[CompanyRef.model_validate(x) for x in c.get("companies", [])],
        asset_ids=asset_ids,
        channels=[NewsChannel.model_validate(x) for x in c.get("channels", [])],
        causal_chain=list(c.get("causal_chain", [])),
        relevance=Relevance(c.get("relevance", Relevance.LOW.value)),
        estimate=estimate,
    )


def _estimates(
    portfolio_id: str, rows: list[NewsItem]
) -> dict[str, tuple[NewsEstimateOut, list[str]]]:
    assets = _company_assets()
    requests = [
        impact_service.NewsImpactRequest(
            news_id=row.id,
            title=row.title,
            url=row.url,
            published_at=as_utc(row.published_at),
            channels=[
                NewsChannel.model_validate(x) for x in (row.classification or {})["channels"]
            ],
            company_assets=assets,
        )
        for row in rows
        if _is_relevant(row)
    ]
    return impact_service.estimate_news_impacts(portfolio_id, requests)


def list_for_portfolio(
    portfolio_id: str, category: NewsCategory | None, affecting: bool, limit: int
) -> list[NewsItemOut]:
    """Noticias de la más reciente a la más antigua hasta el reloj. Con `affecting`, solo las
    que mueven alguna posición de la cartera (estimadas o medidas). 404 si no existe la cartera."""
    now = clock.now()
    rows = [
        row
        for row in repository.list_items(now - WINDOW, now)
        if category is None
        or (row.classification and row.classification.get("category") == category.value)
    ]
    if affecting:
        rows = [row for row in rows if _is_relevant(row)]
    estimates = _estimates(portfolio_id, rows)
    items: list[NewsItemOut] = []
    for row in rows:
        estimate, asset_ids = estimates.get(row.id, (None, []))
        if estimate is None and row.classification:
            estimate = NewsEstimateOut(status=NewsEstimateStatus.NOT_RELEVANT, as_of=now)
        if affecting and (estimate is None or estimate.status not in _SHOWN):
            continue
        items.append(_out(row, estimate, asset_ids))
        if len(items) >= limit:
            break
    return items


def get_for_portfolio(portfolio_id: str, news_id: str) -> NewsItemOut | None:
    row = repository.get_item(news_id)
    if row is None:
        impact_service.estimate_news_impacts(portfolio_id, [])  # 404 si no existe la cartera
        return None
    estimates = _estimates(portfolio_id, [row])
    estimate, asset_ids = estimates.get(row.id, (None, []))
    if estimate is None and row.classification:
        estimate = NewsEstimateOut(status=NewsEstimateStatus.NOT_RELEVANT, as_of=clock.now())
    return _out(row, estimate, asset_ids)
