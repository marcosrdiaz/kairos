"""Una pasada de la ingesta de noticias (T4-28): lee las fuentes y guarda lo nuevo.

- Google Noticias (RSS de búsqueda, edición España), entre `start` y `end`: histórico y diario.
- GDELT (opcional, `use_gdelt`): lo mismo en inglés; muy limitado en peticiones.
- RSS de Yahoo Finance y de la Reserva Federal: solo lo último; se leen si `end` es reciente.

Un fallo de una fuente o de una búsqueda se apunta en el informe y no para al resto. Si una fuente
nos limita (429 o 503), se deja de pedirle en esa pasada y se apunta en `limited`: no se esquivan
bloqueos (D-098). `SourceSchedule` decide cuándo vuelve a tocar cada fuente (TB-01).
"""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import httpx

from app.core import clock
from app.news import repository
from app.news.ingest import gdelt, google, rss, topics
from app.news.ingest.sources import RawNews

log = logging.getLogger(__name__)

TIMEOUT_S = 30.0
USER_AGENT = "Kairos/0.1 (hackathon BEST UC3M; noticias para inversores)"
RSS_RECENT = timedelta(days=2)
"""Los RSS solo traen lo último: se leen si el periodo acaba hace menos de esto."""
RATE_LIMIT_RETRY_S = 12.0
LIMITED_STATUS = frozenset({429, 503})
"""Respuestas con las que una fuente nos pide que paremos."""
MAX_BACKOFF = timedelta(hours=1)

Sleep = Callable[[float], None]


@dataclass
class NewsIngestReport:
    created: list[str] = field(default_factory=list)
    read: int = 0
    failed: dict[str, str] = field(default_factory=dict)
    """Búsqueda o fuente → motivo."""
    limited: set[str] = field(default_factory=set)
    """Fuentes (`google`, `rss`) que nos han limitado en esta pasada."""


@dataclass
class SourceSchedule:
    """Cuándo vuelve a tocar una fuente: cada `interval` y, si nos limita, el doble de la última
    espera (hasta `MAX_BACKOFF`). Una pasada sin límite vuelve al intervalo normal."""

    interval: timedelta
    next_at: datetime | None = None
    wait: timedelta | None = None

    def is_due(self, now: datetime) -> bool:
        return self.next_at is None or now >= self.next_at

    def succeeded(self, now: datetime) -> None:
        self.wait = None
        self.next_at = now + self.interval

    def limited(self, now: datetime) -> None:
        self.wait = min((self.wait or self.interval) * 2, MAX_BACKOFF)
        self.next_at = now + self.wait


def _is_limited(error: Exception) -> bool:
    return isinstance(error, httpx.HTTPStatusError) and error.response.status_code in LIMITED_STATUS


def _http() -> httpx.Client:
    return httpx.Client(
        timeout=TIMEOUT_S, follow_redirects=True, headers={"User-Agent": USER_AGENT}
    )


def _get(http: httpx.Client, url: str) -> str:
    response = http.get(url)
    response.raise_for_status()
    return response.text


def _fail(report: NewsIngestReport, name: str, error: Exception) -> None:
    report.failed[name] = str(error)[:200] or type(error).__name__


def _google(
    http: httpx.Client, start: datetime, end: datetime, sleep: Sleep, report: NewsIngestReport
) -> list[RawNews]:
    found: list[RawNews] = []
    for index, (key, search) in enumerate(topics.google_searches()):
        if index:
            sleep(google.MIN_INTERVAL_S)
        url = google.search_url(search, start.date(), end.date())
        try:
            found.extend(google.parse(_get(http, url), key))
        except (httpx.HTTPError, ValueError) as error:  # ET.ParseError es un ValueError
            _fail(report, f"google:{key}", error)
            if _is_limited(error):
                report.limited.add("google")
                break  # nos ha limitado: no seguimos con el resto de búsquedas
    return found


def _gdelt(
    http: httpx.Client, start: datetime, end: datetime, sleep: Sleep, report: NewsIngestReport
) -> list[RawNews]:
    found: list[RawNews] = []
    for index, (key, search, language) in enumerate(topics.gdelt_searches()):
        if index:
            sleep(gdelt.MIN_INTERVAL_S)
        url = gdelt.query_url(search, language, start, end)
        try:
            try:
                found.extend(gdelt.parse(_get(http, url), key))
            except (httpx.HTTPStatusError, ValueError):  # límite: se espera y se repite una vez
                sleep(RATE_LIMIT_RETRY_S)
                found.extend(gdelt.parse(_get(http, url), key))
        except (httpx.HTTPError, ValueError) as error:
            _fail(report, f"gdelt:{key}:{language}", error)
    return found


def _rss(http: httpx.Client, report: NewsIngestReport) -> list[RawNews]:
    found: list[RawNews] = []
    for symbol in topics.yahoo_symbols():
        try:
            found.extend(rss.parse_yahoo(_get(http, rss.yahoo_url([symbol])), [symbol]))
        except (httpx.HTTPError, ValueError) as error:
            _fail(report, f"yahoo_rss:{symbol}", error)
            if _is_limited(error):
                report.limited.add("rss")
                break
    try:
        found.extend(rss.parse_fed(_get(http, rss.FED_URL)))
    except (httpx.HTTPError, ValueError) as error:
        _fail(report, "fed_rss", error)
        if _is_limited(error):
            report.limited.add("rss")
    return found


def run_once(
    start: datetime,
    end: datetime,
    *,
    http: httpx.Client | None = None,
    sleep: Sleep = time.sleep,
    use_google: bool = True,
    use_gdelt: bool = False,
    use_rss: bool = True,
) -> NewsIngestReport:
    """Lee las fuentes del periodo y guarda las noticias nuevas (sin duplicados)."""
    report = NewsIngestReport()
    client = http or _http()
    try:
        found: list[RawNews] = []
        if use_google:
            found.extend(_google(client, start, end, sleep, report))
        if use_gdelt:
            found.extend(_gdelt(client, start, end, sleep, report))
        if use_rss and clock.now() - end <= RSS_RECENT:
            found.extend(_rss(client, report))
    finally:
        if http is None:
            client.close()
    in_period = [raw for raw in found if start <= raw.published_at <= end]
    report.read = len(in_period)
    report.created = repository.save_new(in_period, clock.now())
    for name, reason in report.failed.items():
        log.warning("Ingesta de noticias: %s falló: %s", name, reason)
    return report
