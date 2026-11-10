"""Interfaz pública de `events`: control del replay (diseño del MVP §4.6) y entrada de eventos
reales con su shock medido (T4-04, D-089).

- `ingest(event, companies)`: procesa un evento real. Si no trae `observed`, se mide con los
  cierres de `prices` (`events/observed.py`); si su sesión aún no ha cerrado, queda pendiente de
  cierre: se guarda con su análisis y sin cifras.
- `process_pending()`: tras el cierre (lo llama `scripts/daily_update.py`), mide y procesa los
  pendientes que ya se pueden medir.

La sesión de hoy nunca se da por cerrada (como en `prices/factors.py`) y el BCE publica la
rentabilidad al día siguiente, así que un evento del día D tiene cifras a partir de D+1.
"""

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.config import get_settings
from app.core import clock
from app.core.errors import AppError, ErrorCode
from app.events import observed, repository
from app.prices import service as prices_service
from app.schemas.common import Factor, SourceKind, SourceRef
from app.schemas.events import (
    EventAnalysis,
    EventIn,
    EventObserved,
    EventStatus,
    PendingEventOut,
    ReplayOut,
    ReplayRequest,
)

log = logging.getLogger(__name__)

REPLAY_DIR = Path(__file__).resolve().parents[3] / "data" / "events" / "replay"
PRELOAD_EVENT_IDS = ("bce-2025-06", "oil-2025-06")
_PRELOAD_AGE = timedelta(hours=96)


def _replay_path(event_id: str) -> Path | None:
    return {path.stem: path for path in REPLAY_DIR.glob("*.json")}.get(event_id)


def _load_replay(event_id: str) -> EventIn:
    path = _replay_path(event_id)
    if path is None:
        raise AppError(ErrorCode.NOT_FOUND, "No existe ese evento.", details={"event_id": event_id})
    return EventIn.model_validate(json.loads(path.read_text(encoding="utf-8")))


def _load(event_id: str) -> EventIn:
    """Del replay o, si no, un evento real guardado (T4-04)."""
    if _replay_path(event_id) is None:
        real = repository.get_payload(event_id)
        if real is not None:
            return real
    return _load_replay(event_id)


def get_event(event_id: str) -> EventIn:
    """Evento del replay o real. Si ya se ha inyectado, con la fecha que se le dio al inyectarlo."""
    event = _load(event_id)
    occurred_at = repository.get_occurred_at(event_id)
    if occurred_at is None:
        return event
    # SQLite devuelve la fecha sin zona; en BD siempre es UTC.
    utc = occurred_at if occurred_at.tzinfo else occurred_at.replace(tzinfo=UTC)
    return event.model_copy(update={"occurred_at": utc})


def get_market_date(event_id: str) -> datetime:
    """Fecha real del evento en el mercado (la del JSON del replay), aunque se haya inyectado
    con otra fecha. Es el día de los precios con los que se mide su movimiento."""
    return _load(event_id).occurred_at


def replay(event_id: str, request: ReplayRequest | None = None) -> ReplayOut:
    """Inyecta un evento del modo replay. Solo con `DEMO_MODE=true`."""
    if not get_settings().demo_mode:
        raise AppError(ErrorCode.DEMO_MODE_DISABLED, "El modo demo está desactivado.")
    from app.events import pipeline  # aquí para evitar el ciclo events → impact → events

    options = request or ReplayRequest()
    return pipeline.run(_load_replay(event_id), options.occurred_at, options.silent)


def preload() -> list[str]:
    """Precarga del guion: BCE y petróleo, fuera de las 72 h de Atento y sin gastar avisos."""
    occurred_at = clock.now() - _PRELOAD_AGE
    request = ReplayRequest(occurred_at=occurred_at, silent=True)
    for event_id in PRELOAD_EVENT_IDS:
        replay(event_id, request)
    return list(PRELOAD_EVENT_IDS)


OBSERVED_SOURCE = "Cierres de Yahoo Finance y del BCE: sesión del evento frente a la anterior"
_COMPANY_LOOKBACK = timedelta(days=30)


def measure_observed(event: EventIn, companies: dict[str, str]) -> EventObserved | None:
    """Shock medido del evento con los cierres de `prices` (`companies`: clave → `asset_id`).
    `None` si la sesión que lo recoge aún no ha cerrado para todos los factores y empresas."""
    today = clock.now().date()
    day = observed.reaction_date(event.occurred_at)
    if day >= today:
        return None
    factor_series = {
        factor: [(p.day, p.value) for p in prices_service.factor_closes(factor) if p.day < today]
        for factor in Factor
    }
    company_series = {
        key: [
            (p.price_at.date(), p.price)
            for p in prices_service.history(asset_id, day - _COMPANY_LOOKBACK, today)
            if p.price_at.date() < today
        ]
        for key, asset_id in companies.items()
    }
    return observed.measure(day, factor_series, company_series)


def ingest(event: EventIn, companies: dict[str, str] | None = None) -> ReplayOut | None:
    """Procesa un evento real (no replay). Devuelve `None` si queda pendiente de cierre."""
    from app.events import pipeline  # aquí por el ciclo events → impact → events

    links = dict(companies or {})
    if event.observed is None:
        measured = measure_observed(event, links)
        if measured is None:
            pipeline.save_pending(event, links)
            return None
        event = event.model_copy(update={"observed": measured, "observed_source": OBSERVED_SOURCE})
    result = pipeline.run(event, event.occurred_at, silent=False, replay=False)
    repository.delete_pending(event.id)
    return result


def process_pending() -> list[str]:
    """Mide y procesa los eventos pendientes cuya sesión ya ha cerrado. Un fallo en uno se
    registra y no para el resto. Devuelve los ids procesados."""
    processed: list[str] = []
    for event, companies in repository.list_pending():
        try:
            if measure_observed(event, companies) is None:
                continue
            if ingest(event, companies) is not None:
                processed.append(event.id)
        except Exception:
            log.exception("No se pudo procesar el evento pendiente %s", event.id)
    return processed


def list_pending() -> list[str]:
    return [event.id for event, _ in repository.list_pending()]


def list_pending_out() -> list[PendingEventOut]:
    """`GET /events/pending`: cada pendiente con la cadena causal de su análisis guardado (o la
    de respaldo del evento) y sus fuentes. Sin ninguna cifra."""
    out: list[PendingEventOut] = []
    for event, _ in repository.list_pending():
        analysis = repository.get_analysis(event.id)
        chain = analysis.causal_chain if analysis is not None else event.fallback_chain
        sources = [
            SourceRef(
                kind=SourceKind.EVENT,
                label=f"Noticia: {event.title}",
                ref=event.id,
                as_of=event.occurred_at,
                url=url,
            )
            for url in event.source_urls
        ]
        out.append(
            PendingEventOut(
                event_id=event.id,
                title=event.title,
                event_type=event.type,
                occurred_at=event.occurred_at,
                causal_chain=chain,
                status=EventStatus.PENDING_CLOSE,
                sources=sources,
            )
        )
    return out


def get_analysis(event_id: str) -> EventAnalysis | None:
    """Análisis guardado del evento (cadena causal incluida), también si está pendiente."""
    return repository.get_analysis(event_id)


def reset() -> None:
    """Borra los eventos. Antes hay que llamar a `impact.service.reset`."""
    from app.agents import service as agents_service  # aquí por el mismo ciclo que `replay`

    repository.delete_all()
    agents_service.invalidate_context()
