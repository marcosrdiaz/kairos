"""Mock de los agentes: sirve los ejemplos de `schemas/examples/` (D-018).

Lo sustituyen T1-16 (guardián) y T1-17 (explicador); se borra en T2-03.
"""

from collections.abc import Iterator

from app.schemas import examples
from app.schemas.agents import (
    AskDoneEvent,
    AskEvent,
    AskMetaEvent,
    AskSentenceEvent,
    EventImpactStub,
    ExplainerContext,
    ExplanationStatus,
    SentenceStatus,
    StatusFacts,
)

# Textos sin cifras: el mock nunca inventa números (regla 1 de producto).
_EVENT_EXPLANATION = (
    "Este evento afecta a tu cartera. Abre el detalle para ver cómo y de dónde sale."
)
_STATUS_SENTENCE = "Hay novedades en tu cartera. Toca para ver por qué."
_ALERT_MESSAGE = "Ha pasado algo que afecta a tu cartera. Abre KAIROS para verlo."


def ask_events() -> Iterator[AskEvent]:
    """Turno completo de ejemplo: meta, dos frases y done."""
    yield AskMetaEvent.model_validate(examples.load("AskMetaEvent"))
    yield AskSentenceEvent.model_validate(examples.load("AskSentenceEvent"))
    yield AskSentenceEvent.model_validate(examples.load("AskSentenceEvent.impact"))
    yield AskDoneEvent.model_validate(examples.load("AskDoneEvent"))


def explainer_context(portfolio_id: str) -> ExplainerContext:
    context = ExplainerContext.model_validate(examples.load("ExplainerContext"))
    return context.model_copy(update={"portfolio_id": portfolio_id})


def write_event_explanation(impact: EventImpactStub) -> tuple[str, ExplanationStatus]:
    return _EVENT_EXPLANATION, ExplanationStatus.TEMPLATE


def write_status_sentence(facts: StatusFacts) -> tuple[str, SentenceStatus]:
    return _STATUS_SENTENCE, SentenceStatus.TEMPLATE


def write_alert_message(impact: EventImpactStub) -> str:
    return _ALERT_MESSAGE
