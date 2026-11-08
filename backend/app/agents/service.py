"""Interfaz pública de los agentes (diseño del MVP §4.4).

Otros módulos importan solo `write_event_explanation`, `write_status_sentence` y
`write_alert_message`. De momento todo delega en `mock.py`; T1-17 cambia cada función a la
implementación real sin cambiar su firma.
"""

from collections.abc import Iterator

from app.agents import mock
from app.portfolio import service as portfolio_service
from app.schemas.agents import (
    AskEvent,
    AskRequest,
    EventImpactStub,
    ExplainerContext,
    ExplanationStatus,
    SentenceStatus,
    StatusFacts,
)

# --- Interfaz entre módulos ---


def write_event_explanation(impact: EventImpactStub) -> tuple[str, ExplanationStatus]:
    return mock.write_event_explanation(impact)


def write_status_sentence(facts: StatusFacts) -> tuple[str, SentenceStatus]:
    return mock.write_status_sentence(facts)


def write_alert_message(impact: EventImpactStub) -> str:
    return mock.write_alert_message(impact)


# --- Uso de `api/ask.py` ---


def ask(portfolio_id: str, request: AskRequest) -> Iterator[AskEvent]:
    """Eventos SSE del turno. Falla con NOT_FOUND antes de emitir nada si la cartera no existe."""
    portfolio_service.ensure_exists(portfolio_id)
    return mock.ask_events()


def get_explainer_context(portfolio_id: str) -> ExplainerContext:
    portfolio_service.ensure_exists(portfolio_id)
    return mock.explainer_context(portfolio_id)
