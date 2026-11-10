"""Una pasada de la ingesta de noticias (T4-05): lee las fuentes, descarta lo ya visto (clave: URL)
y da de alta cada evento nuevo con `events.service.ingest`, que lo mide o lo deja pendiente de
cierre (D-096).

Solo en producción (`DEMO_MODE=false`): en modo demo los eventos salen del replay. Un fallo de una
fuente o de una nota se registra y no para al resto.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import timedelta

import httpx

from app.config import get_settings
from app.core import clock
from app.events import repository
from app.events.ingest import ecb
from app.schemas.events import EventIn, ReplayOut

log = logging.getLogger(__name__)

TIMEOUT_S = 10.0
MAX_AGE = timedelta(days=30)
"""Una nota más antigua no se da de alta (p. ej. al arrancar con la BD vacía)."""

Ingest = Callable[[EventIn, dict[str, str] | None], ReplayOut | None]


@dataclass
class IngestReport:
    created: list[str] = field(default_factory=list)
    """Eventos nuevos dados de alta (medidos o pendientes de cierre)."""
    skipped: list[str] = field(default_factory=list)
    """Ya vistos: misma URL que un evento guardado."""
    failed: dict[str, str] = field(default_factory=dict)
    """URL o fuente → motivo."""


def _default_ingest(event: EventIn, companies: dict[str, str] | None) -> ReplayOut | None:
    from app.events import service  # aquí por el ciclo events.service → pipeline → …

    return service.ingest(event, companies)


def _http() -> httpx.Client:
    return httpx.Client(
        timeout=TIMEOUT_S, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}
    )


def _get(http: httpx.Client, url: str) -> str:
    response = http.get(url)
    response.raise_for_status()
    return response.text


def _release(http: httpx.Client, url: str) -> tuple[str, str, str]:
    """`(título, texto, url)` de la nota, en español si el BCE ya la ha traducido."""
    spanish = ecb.language_url(url, "es")
    try:
        return (*ecb.parse_release(_get(http, spanish)), spanish)
    except (httpx.HTTPError, ValueError):
        return (*ecb.parse_release(_get(http, url)), url)


def _ingest_ecb(http: httpx.Client, ingest: Ingest, report: IngestReport) -> None:
    try:
        items = ecb.parse_feed(_get(http, ecb.FEED_URL))
    except (httpx.HTTPError, ValueError) as error:  # ET.ParseError es un ValueError
        report.failed[ecb.FEED_URL] = str(error) or type(error).__name__
        return
    now = clock.now()
    for item in items:
        if not ecb.is_policy_decision(item.url) or not now - MAX_AGE <= item.published <= now:
            continue
        event_id = ecb.event_id(item.url)
        if repository.get_occurred_at(event_id) is not None:
            report.skipped.append(event_id)
            continue
        try:
            title, text, url = _release(http, item.url)
            ingest(ecb.build_event(item, title, text, url), None)
        except Exception as error:
            log.exception("No se pudo dar de alta la nota del BCE %s", item.url)
            report.failed[item.url] = str(error) or type(error).__name__
            continue
        report.created.append(event_id)


def run_once(http: httpx.Client | None = None, ingest: Ingest | None = None) -> IngestReport:
    report = IngestReport()
    if get_settings().demo_mode:
        log.info("Modo demo: la ingesta de noticias no hace nada (los eventos salen del replay)")
        return report
    client = http or _http()
    try:
        _ingest_ecb(client, ingest or _default_ingest, report)
    finally:
        if http is None:
            client.close()
    return report
