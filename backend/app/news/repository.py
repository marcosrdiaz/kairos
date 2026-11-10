"""Acceso a la tabla `news_item`. Solo aquí se consulta."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select

from app.core.db import session_scope
from app.news.ingest.sources import RawNews, news_id, title_key, url_key
from app.news.models import NewsItem

DUPLICATE_TITLE_WINDOW_S = 3 * 24 * 3600
"""El mismo titular en otro medio dentro de este margen es la misma noticia."""


def as_utc(value: datetime) -> datetime:
    """SQLite devuelve las fechas sin zona; en BD siempre son UTC."""
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _is_duplicate(raw: RawNews, keys: dict[str, list[datetime]], seen_urls: set[str]) -> bool:
    if url_key(raw.url) in seen_urls:
        return True
    return any(
        abs((raw.published_at - when).total_seconds()) <= DUPLICATE_TITLE_WINDOW_S
        for when in keys.get(title_key(raw.title), [])
    )


def save_new(items: list[RawNews], fetched_at: datetime) -> list[str]:
    """Guarda las que no están ya (misma URL o mismo titular en pocos días). Devuelve sus ids."""
    if not items:
        return []
    created: list[str] = []
    with session_scope() as session:
        url_keys = {url_key(raw.url) for raw in items}
        title_keys = {title_key(raw.title) for raw in items}
        seen_urls = set(
            session.scalars(select(NewsItem.url_key).where(NewsItem.url_key.in_(url_keys)))
        )
        keys: dict[str, list[datetime]] = {}
        rows = session.execute(
            select(NewsItem.title_key, NewsItem.published_at).where(
                NewsItem.title_key.in_(title_keys)
            )
        )
        for key, when in rows:
            keys.setdefault(key, []).append(as_utc(when))
        for raw in sorted(items, key=lambda r: r.published_at):
            if _is_duplicate(raw, keys, seen_urls):
                continue
            row = NewsItem(
                id=news_id(raw.url),
                url=raw.url,
                url_key=url_key(raw.url),
                title_key=title_key(raw.title),
                title=raw.title[:500],
                summary=raw.summary,
                published_at=raw.published_at,
                source_name=raw.source_name,
                provider=raw.provider,
                language=raw.language,
                query=raw.query[:300],
                fetched_at=fetched_at,
            )
            session.add(row)
            seen_urls.add(row.url_key)
            keys.setdefault(row.title_key, []).append(raw.published_at)
            created.append(row.id)
    return created


def list_items(start: datetime | None = None, end: datetime | None = None) -> list[NewsItem]:
    """Noticias de la más reciente a la más antigua, opcionalmente entre `start` y `end`."""
    with session_scope() as session:
        stmt = select(NewsItem).order_by(NewsItem.published_at.desc())
        if start is not None:
            stmt = stmt.where(NewsItem.published_at >= start)
        if end is not None:
            stmt = stmt.where(NewsItem.published_at <= end)
        rows = list(session.scalars(stmt))
        session.expunge_all()
        return rows


def get_item(item_id: str) -> NewsItem | None:
    with session_scope() as session:
        row = session.get(NewsItem, item_id)
        if row is not None:
            session.expunge(row)
        return row


def unclassified(classifier_key: str, limit: int) -> list[NewsItem]:
    """Sin clasificar o clasificadas con otra versión del clasificador; las más recientes antes."""
    with session_scope() as session:
        stmt = (
            select(NewsItem)
            .where(
                (NewsItem.classifier_key.is_(None)) | (NewsItem.classifier_key != classifier_key)
            )
            .order_by(NewsItem.published_at.desc())
            .limit(limit)
        )
        rows = list(session.scalars(stmt))
        session.expunge_all()
        return rows


def save_classification(
    item_id: str, classification: dict[str, Any], classifier_key: str, at: datetime
) -> None:
    with session_scope() as session:
        row = session.get(NewsItem, item_id)
        if row is None:
            return
        row.classification = classification
        row.classifier_key = classifier_key
        row.classified_at = at


def delete_all() -> None:
    with session_scope() as session:
        session.execute(delete(NewsItem))
