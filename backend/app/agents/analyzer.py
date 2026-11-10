"""Analizador de eventos (`SPEC.md` §9, diseño del MVP §4.2).

Clasifica el evento, describe los canales y redacta la cadena causal. No recibe ni produce
magnitudes: salen de `observed` (D-025) y las cifras usan siempre todos los factores observados
(D-083), así que los canales solo sirven para la narrativa.

Recibe la **dirección** observada de cada factor (sube o baja, sin cuánto). Tras la respuesta,
`channels[].direction` se corrige al signo observado; si la cadena causal contradice un dato
observado, se reintenta con ese motivo como feedback. Si falla tras el reintento lanza
`AnalyzerError` y `events` usa el análisis de respaldo.
"""

import hashlib
from pathlib import Path
from typing import Any

import anthropic
from pydantic import ValidationError, field_validator

from app.agents import analyzer_directions, guardian
from app.config import get_settings
from app.schemas.common import ContractModel
from app.schemas.events import (
    Channel,
    CompanyRef,
    Entity,
    EventAnalysis,
    EventIn,
    EventType,
    Relevance,
    _no_digits,
)

_PROMPT_PATH = Path(__file__).parent / "prompts" / "analyzer.md"
_ATTEMPTS = 2
_TIMEOUT_S = 10.0
"""Con Claude real las llamadas tardaban 3–4 s y con 4 s se agotaban los dos intentos (D-083)."""
_MAX_TOKENS = 2048


def _prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def prompt_version() -> str:
    """Primeros 12 hex del SHA-256 del prompt: cambia en cuanto cambia el prompt (T2-26)."""
    return hashlib.sha256(_prompt().encode("utf-8")).hexdigest()[:12]


def input_key(event: EventIn) -> str:
    """Clave de caché del análisis: versión del prompt y huella de lo que se le envía al modelo.
    Si cambia cualquiera de los dos, el análisis guardado deja de valer."""
    message = hashlib.sha256(_user_message(event, None).encode("utf-8")).hexdigest()[:12]
    return f"{prompt_version()}:{message}"


class AnalyzerError(Exception):
    """El analizador no ha dado un resultado válido."""


class AnalyzerDraft(ContractModel):
    """Lo que escribe el modelo. El resto de `EventAnalysis` lo pone el código."""

    event_type: EventType
    entities: list[Entity]
    channels: list[Channel]
    companies: list[CompanyRef]
    causal_chain: list[str]
    relevance: Relevance

    @field_validator("causal_chain")
    @classmethod
    def _chain_has_no_digits(cls, value: list[str]) -> list[str]:
        for step in value:
            _no_digits(step)
        return value


_client: Any | None = None


def set_client(client: Any | None) -> None:
    """Sustituye el cliente de Claude (tests). `None` vuelve al real."""
    global _client
    _client = client


def _get_client() -> Any:
    if _client is not None:
        return _client
    api_key = get_settings().anthropic_api_key
    if not api_key:
        raise AnalyzerError("Falta ANTHROPIC_API_KEY")
    return anthropic.Anthropic(api_key=api_key, timeout=_TIMEOUT_S, max_retries=0)


def _user_message(event: EventIn, feedback: str | None) -> str:
    observed = event.observed
    factors = analyzer_directions.describe(observed.factors) if observed else "ninguno"
    companies = analyzer_directions.describe(observed.companies) if observed else "ninguna"
    parts = [
        f"Tipo indicado: {event.type.value}",
        f"Título: {event.title}",
        f"Movimiento observado de cada factor ese día (solo la dirección): {factors}",
        f"Empresas disponibles y su movimiento observado: {companies or 'ninguna'}",
    ]
    if event.consensus is not None:
        consensus = event.consensus
        parts.append(
            f"Consenso ({consensus.metric}): esperado {consensus.expected}, real {consensus.actual}"
        )
    parts.append(f"<evento>\n{event.text}\n</evento>")
    if feedback:
        parts.append(f"El intento anterior no fue válido ({feedback}). Corrígelo.")
    return "\n".join(parts)


def _check_no_orders(draft: AnalyzerDraft) -> None:
    """Los textos del analizador llegan al usuario (regla 3 de producto): patrones del guardián.

    Solo los patrones: el borrador no lleva cifras (D-025) ni tiene evidencias con las que
    comprobarlas, y la forma que mira `guardian.check` es la de las respuestas del explicador.
    """
    texts = [
        *draft.causal_chain,
        *(c.label for c in draft.channels),
        *(c.rationale for c in draft.channels),
    ]
    if any(guardian.find_forbidden(text) for text in texts):
        raise ValueError("el texto contiene una orden o un consejo de inversión")


def _attempt(client: Any, event: EventIn, model: str, feedback: str | None) -> AnalyzerDraft:
    response = client.messages.parse(
        model=model,
        max_tokens=_MAX_TOKENS,
        output_config={"effort": "low"},
        system=_prompt(),
        messages=[{"role": "user", "content": _user_message(event, feedback)}],
        output_format=AnalyzerDraft,
    )
    draft = response.parsed_output
    if response.stop_reason == "refusal" or draft is None:
        raise ValueError(f"sin resultado ({response.stop_reason})")
    _check_no_orders(draft)
    if event.observed is not None:
        analyzer_directions.check_chain(draft.causal_chain, event.observed.factors)
        channels = analyzer_directions.correct(draft.channels, event.observed.factors)
        draft = draft.model_copy(update={"channels": channels})
    return draft  # type: ignore[no-any-return]


def analyze(event: EventIn) -> EventAnalysis:
    client = _get_client()
    model = get_settings().anthropic_model_deep
    feedback: str | None = None
    for _ in range(_ATTEMPTS):
        try:
            draft = _attempt(client, event, model, feedback)
        except (anthropic.AnthropicError, ValidationError, ValueError, RuntimeError) as error:
            feedback = type(error).__name__ if isinstance(error, ValidationError) else str(error)
            continue
        return EventAnalysis(
            schema_version=1,
            event_id=event.id,
            event_type=draft.event_type,
            entities=draft.entities,
            channels=draft.channels,
            companies=draft.companies,
            causal_chain=draft.causal_chain,
            relevance=draft.relevance,
            analyzed_model=model,
            fallback=False,
            prompt_version=prompt_version(),
        )
    raise AnalyzerError(feedback or "sin resultado")
