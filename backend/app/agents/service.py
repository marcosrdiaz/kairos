"""Interfaz pública de los agentes (diseño del MVP §4.4).

Otros módulos importan `analyze_event`, `write_event_explanation`, `write_status_sentence`,
`write_alert_message` e `invalidate_context`. Todo texto sale validado por el guardián
(regla 3 de producto); si el modelo no está o se bloquea dos veces, sale de plantilla.
"""

from collections.abc import Iterator
from threading import Lock

from app.agents import analyzer, context, explainer, templates, writer
from app.agents.fact_format import text_evidence
from app.agents.facts import status_facts, stub_facts
from app.portfolio import service as portfolio_service
from app.schemas.agents import (
    AskEvent,
    AskRequest,
    EventImpactStub,
    ExplainerContext,
    ExplanationStatus,
    GuardianChannel,
    QuestionKind,
    SentenceStatus,
    StatusFacts,
)
from app.schemas.events import EventAnalysis, EventIn

# Una tarea por canal; el redactor comprueba la longitud con `writer.LIMITS`.
_EVENT_TASK = (
    "Texto: explicación de un evento en el panel. Como mucho 2 frases y 60 palabras. La primera "
    "dice cuánto le afecta en euros y si es a favor o en contra, con el rango; la segunda, por "
    "qué canal le llega, a partir de esta cadena causal: {chain}. Evento: «{title}»."
)
_STATUS_TASK = (
    "Texto: frase del widget de la pantalla de inicio. Una sola frase de 15 palabras como mucho "
    "que diga cómo está la cartera; si el estado es atento o revisa_plan, puedes añadir detrás "
    "«Toca para ver por qué.». Estado: {state}. {detail}"
)
_ALERT_TASK = (
    "Texto: aviso al móvil. Una sola frase de 20 palabras como mucho con el evento y cuánto "
    "afecta a la cartera en euros. Evento: «{title}»."
)

_sessions: set[str] = set()
_sessions_lock = Lock()

# --- Interfaz entre módulos ---


def analyze_event(event: EventIn) -> EventAnalysis:
    """Lanza `analyzer.AnalyzerError` si falla tras el reintento; `events` usa el respaldo."""
    return analyzer.analyze(event)


def write_event_explanation(impact: EventImpactStub) -> tuple[str, ExplanationStatus]:
    task = _EVENT_TASK.format(chain=" → ".join(impact.causal_chain), title=impact.title)
    text, by_model = writer.write(
        GuardianChannel.EVENT_EXPLANATION,
        task,
        stub_facts(impact),
        templates.event_explanation(impact),
        kind=QuestionKind.IMPACT,
        extra_evidence=text_evidence([impact.title], f"event:{impact.event_id}"),
    )
    return text, ExplanationStatus.OK if by_model else ExplanationStatus.TEMPLATE


def write_status_sentence(facts: StatusFacts) -> tuple[str, SentenceStatus]:
    detail = f"Evento: «{facts.event_title}»." if facts.event_title else ""
    task = _STATUS_TASK.format(state=facts.state.value, detail=detail)
    source = f"event:{facts.reason.event_id}" if facts.reason.event_id else "status"
    text, by_model = writer.write(
        GuardianChannel.WIDGET,
        task,
        status_facts(facts),
        templates.status_sentence(facts),
        extra_evidence=text_evidence([facts.event_title], source),
    )
    return text, SentenceStatus.OK if by_model else SentenceStatus.TEMPLATE


def write_alert_message(impact: EventImpactStub) -> str:
    text, _ = writer.write(
        GuardianChannel.ALERT,
        _ALERT_TASK.format(title=impact.title),
        stub_facts(impact),
        templates.alert_message(impact),
        kind=QuestionKind.IMPACT,
        extra_evidence=text_evidence([impact.title], f"event:{impact.event_id}"),
    )
    return text


def invalidate_context(portfolio_id: str | None = None) -> None:
    """Olvida el contexto precargado del explicador (T2-09 la llama tras cada evento)."""
    context.invalidate(portfolio_id)


# --- Uso de `api/ask.py` ---


def _first_time(session_id: str) -> bool:
    """`True` la primera vez que se ve la sesión: toca el aviso de IA (AI Act art. 50)."""
    with _sessions_lock:
        if session_id in _sessions:
            return False
        _sessions.add(session_id)
        return True


def ask(portfolio_id: str, request: AskRequest) -> Iterator[AskEvent]:
    """Eventos SSE del turno. Falla con NOT_FOUND antes de emitir nada si la cartera no existe."""
    portfolio_service.ensure_exists(portfolio_id)
    turn = explainer.Turn(portfolio_id, request, disclaimer=_first_time(request.session_id))
    return turn.events()


def get_explainer_context(portfolio_id: str) -> ExplainerContext:
    portfolio_service.ensure_exists(portfolio_id)
    return context.get(portfolio_id).context
