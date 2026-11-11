"""Interfaz pública de `news` (hito E).

- `ingest`: lee las fuentes reales de un periodo y guarda lo nuevo (T4-28).
- `refresh`: una pasada incremental de las fuentes a las que les toca (TB-01, cada 5 minutos).
- `export_snapshot` / `load_snapshot`: la base de noticias de `data/news/` (JSON Lines), para que
  `make up` arranque con las noticias ya cargadas y clasificadas, sin red ni claves.
"""

import json
import logging
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from app.agents import news_classifier
from app.core import clock
from app.core.errors import AppError, ErrorCode
from app.news import portfolio_view, repository
from app.news.ingest import runner, topics
from app.news.ingest.sources import RawNews, news_id
from app.news.models import NewsItem
from app.news.repository import as_utc
from app.schemas.news import NewsCategory, NewsItemOut

NEWS_DIR = Path(__file__).resolve().parents[3] / "data" / "news"
log = logging.getLogger(__name__)

NewsIngestReport = runner.NewsIngestReport
SourceSchedule = runner.SourceSchedule

REFRESH_OVERLAP = timedelta(days=1)
"""La pasada vuelve a mirar al menos el último día: Google busca por días y publica con retraso."""
REFRESH_MAX_GAP = timedelta(days=7)
"""Si la ingesta ha estado parada, recupera como mucho esto hacia atrás."""

_refresh_lock = threading.Lock()


@contextmanager
def refresh_lock() -> Iterator[None]:
    """El cerrojo de `refresh`, ocupado mientras dura el bloque (tests)."""
    with _refresh_lock:
        yield


def refresh_window(now: datetime) -> tuple[datetime, datetime]:
    """Desde la última noticia guardada (con `REFRESH_OVERLAP` de solape y como mucho
    `REFRESH_MAX_GAP` atrás) hasta ahora. Sin noticias recientes (base vacía o ingesta parada más
    de una semana), la última semana."""
    oldest = now - REFRESH_MAX_GAP
    recent = repository.list_items(oldest, now)  # de la más reciente a la más antigua
    latest = as_utc(recent[0].published_at) if recent else oldest
    start = min(now - REFRESH_OVERLAP, latest)
    return max(oldest, start), now


def refresh(
    schedules: dict[str, SourceSchedule],
    *,
    http: httpx.Client | None = None,
    sleep: runner.Sleep = time.sleep,
) -> NewsIngestReport | None:
    """Una pasada de las fuentes a las que les toca (`schedules`: `google` y `rss`) y guarda lo
    nuevo, sin duplicados. Ajusta cuándo vuelve a tocar cada una; si una nos limita, espera más.
    Devuelve `None` si ya hay otra pasada en curso (nunca dos a la vez)."""
    if not _refresh_lock.acquire(blocking=False):
        return None
    try:
        now = clock.now()
        due = {name for name, schedule in schedules.items() if schedule.is_due(now)}
        if not due:
            return NewsIngestReport()
        start, end = refresh_window(now)
        report = runner.run_once(
            start,
            end,
            http=http,
            sleep=sleep,
            use_google="google" in due,
            use_gdelt=False,
            use_rss="rss" in due,
        )
        for name in due:
            if name in report.limited:
                schedules[name].limited(now)
            else:
                schedules[name].succeeded(now)
        return report
    finally:
        _refresh_lock.release()


def ingest(
    start: datetime,
    end: datetime,
    *,
    use_google: bool = True,
    use_gdelt: bool = False,
    use_rss: bool = True,
) -> NewsIngestReport:
    """Noticias reales publicadas entre `start` y `end`, sin duplicados."""
    return runner.run_once(start, end, use_google=use_google, use_gdelt=use_gdelt, use_rss=use_rss)


def list_for_portfolio(
    portfolio_id: str, category: NewsCategory | None = None, affecting: bool = True, limit: int = 50
) -> list[NewsItemOut]:
    """Noticias con su impacto en esta cartera (T4-30). Ver `portfolio_view.py`."""
    return portfolio_view.list_for_portfolio(portfolio_id, category, affecting, limit)


def get_for_portfolio(portfolio_id: str, news_id: str) -> NewsItemOut:
    """Una noticia con su impacto en esta cartera. 404 si no existe la cartera o la noticia."""
    item = portfolio_view.get_for_portfolio(portfolio_id, news_id)
    if item is None:
        raise AppError(ErrorCode.NOT_FOUND, "No encontramos esa noticia.", {"news_id": news_id})
    return item


def known_companies() -> dict[str, str]:
    """Empresas que puede citar el clasificador: clave (ticker) → nombre."""
    return {c.key: c.name for c in topics.COMPANIES}


def classify_pending(limit: int = 1000) -> int:
    """Clasifica con Claude las noticias sin clasificar (o de otra versión del clasificador), por
    lotes. Devuelve cuántas se han clasificado. Sin `ANTHROPIC_API_KEY` no hace nada.

    Llama al clasificador directamente (`agents.news_classifier`) y no por `agents/service.py`,
    que tiene en curso T2-26: se moverá allí cuando T2-26 esté en `main`."""
    key = news_classifier.classifier_key()
    rows = repository.unclassified(key, limit)
    companies = known_companies()
    done = 0
    for start in range(0, len(rows), news_classifier.BATCH_SIZE):
        batch = rows[start : start + news_classifier.BATCH_SIZE]
        inputs = [
            news_classifier.NewsInput(
                index=i,
                title=row.title,
                summary=row.summary,
                source=row.source_name,
                published_at=as_utc(row.published_at),
            )
            for i, row in enumerate(batch)
        ]
        try:
            accepted = news_classifier.classify(inputs, companies)
        except news_classifier.ClassifierError as error:
            log.warning("Clasificador de noticias: lote sin clasificar (%s)", error)
            if "ANTHROPIC_API_KEY" in str(error):
                return done
            continue
        now = clock.now()
        for index, result in accepted.items():
            repository.save_classification(
                batch[index].id, result.model_dump(mode="json"), key, now
            )
            done += 1
    return done


def _row_to_json(row: NewsItem) -> dict[str, Any]:
    return {
        "url": row.url,
        "title": row.title,
        "summary": row.summary,
        "published_at": as_utc(row.published_at).isoformat().replace("+00:00", "Z"),
        "source_name": row.source_name,
        "provider": row.provider,
        "language": row.language,
        "query": row.query,
        "classification": row.classification,
        "classifier_key": row.classifier_key,
    }


def export_snapshot(path: Path, start: datetime | None = None, end: datetime | None = None) -> int:
    """Escribe las noticias guardadas (con su clasificación) en `path`, de la más antigua a la más
    reciente. Devuelve cuántas."""
    rows = sorted(repository.list_items(start, end), key=lambda r: as_utc(r.published_at))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(_row_to_json(row), ensure_ascii=False, sort_keys=True) + "\n")
    return len(rows)


def load_snapshot(directory: Path = NEWS_DIR) -> int:
    """Carga los `*.jsonl` de `directory` (las que ya estén no se duplican). Devuelve cuántas
    noticias nuevas."""
    created = 0
    now = clock.now()
    for path in sorted(directory.glob("*.jsonl")):
        lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
        raws = [
            RawNews(
                url=d["url"],
                title=d["title"],
                summary=d.get("summary", ""),
                published_at=datetime.fromisoformat(d["published_at"]),
                source_name=d["source_name"],
                provider=d["provider"],
                language=d["language"],
                query=d.get("query", ""),
            )
            for d in lines
        ]
        new_ids = set(repository.save_new(raws, now))
        created += len(new_ids)
        for data in lines:
            item_id = news_id(data["url"])
            if item_id in new_ids and data.get("classification"):
                repository.save_classification(
                    item_id, data["classification"], data["classifier_key"], now
                )
    return created
