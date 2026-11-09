"""Textos cortos fuera de `/ask`: explicación de evento, frase del widget y aviso (§4.4).

Mismo esquema que el explicador: Claude rápido redacta con las cifras ya calculadas (prompt
`prompts/writer.md` y una tarea por canal), el guardián valida el texto entero con su canal, se
comprueba la longitud del canal, un reintento con el motivo y, si no, la plantilla (que también
pasa el guardián). Sin clave de Anthropic, directamente la plantilla. Nunca lanza: lo llama el
pipeline de eventos.
"""

import json
import logging
from typing import Any

from app.agents import claude, guardian, templates
from app.agents.fact_format import as_evidence
from app.schemas.agents import (
    Evidence,
    Fact,
    GuardianChannel,
    GuardianRequest,
    GuardianVerdict,
    QuestionKind,
)

ATTEMPTS = 2
LIMITS: dict[GuardianChannel, tuple[int, int]] = {
    GuardianChannel.WIDGET: (2, 22),
    GuardianChannel.ALERT: (1, 25),
    GuardianChannel.EVENT_EXPLANATION: (3, 70),
}
"""Por canal: (frases, palabras) como mucho en el texto del modelo. El widget es una frase corta
de unas 15 palabras, más el «Toca para ver por qué» si toca (producto, §Widget)."""

logger = logging.getLogger(__name__)


def _check(
    text: str, channel: GuardianChannel, kind: QuestionKind | None, evidence: list[Evidence]
) -> GuardianVerdict:
    request = GuardianRequest(
        text=text, channel=channel, question_kind=kind, sentence_index=0, evidence=evidence
    )
    return guardian.check(request)


def too_long(text: str, channel: GuardianChannel) -> str | None:
    """El motivo si el texto se pasa del límite del canal; `None` si cabe."""
    if channel not in LIMITS:
        return None
    max_sentences, max_words = LIMITS[channel]
    sentences = guardian.count_sentences(guardian.normalize(text))
    words = len(text.split())
    if sentences > max_sentences or words > max_words:
        return (
            f"tiene {sentences} frases y {words} palabras; el máximo es {max_sentences} frases "
            f"y {max_words} palabras"
        )
    return None


def _message(task: str, found: list[Fact], feedback: str | None) -> str:
    facts_json = json.dumps([f.model_dump(mode="json") for f in found], ensure_ascii=False)
    parts = [task, f"<facts>\n{facts_json}\n</facts>"]
    if feedback:
        parts.append(
            f"El intento anterior no ha pasado la revisión ({feedback}). Escríbelo de nuevo."
        )
    return "\n".join(parts)


def _complete(client: Any, task: str, found: list[Fact], feedback: str | None) -> str:
    kwargs = {
        **claude.base_kwargs(),
        "system": claude.writer_prompt(),
        "messages": [{"role": "user", "content": _message(task, found, feedback)}],
    }
    with client.messages.stream(**kwargs) as stream:
        return claude.final_text(stream.get_final_message())


def _by_model(
    channel: GuardianChannel,
    task: str,
    found: list[Fact],
    kind: QuestionKind | None,
    evidence: list[Evidence],
) -> str | None:
    client = claude.get_client()
    feedback: str | None = None
    for _ in range(ATTEMPTS if client is not None else 0):
        try:
            text = _complete(client, task, found, feedback)
        except claude.UPSTREAM_ERRORS:
            logger.warning("Redactor (%s): fallo del modelo, plantilla", channel, exc_info=True)
            return None
        except Exception:
            logger.exception("Redactor (%s): error inesperado, plantilla", channel)
            return None
        reasons = [r.detail for r in _check(text, channel, kind, evidence).reasons]
        length = too_long(text, channel)
        if length:
            reasons.append(length)
        if not reasons:
            return text
        feedback = "; ".join(reasons)
        logger.info("Redactor (%s): texto bloqueado: %s", channel, feedback)
    return None


def write(
    channel: GuardianChannel,
    task: str,
    found: list[Fact],
    template: str,
    *,
    kind: QuestionKind | None = None,
    extra_evidence: list[Evidence] | None = None,
) -> tuple[str, bool]:
    """Texto validado y si lo ha escrito el modelo (`True`) o es de plantilla (`False`)."""
    evidence = [*as_evidence(found), *(extra_evidence or [])]
    text = _by_model(channel, task, found, kind, evidence)
    if text is not None:
        return text, True
    if _check(template, channel, kind, evidence).ok:
        return template, False
    logger.warning("Redactor (%s): la plantilla no pasa el guardián: %s", channel, template)
    return templates.SAFE_TEXT, False  # sin cifras ni órdenes: un test comprueba que pasa
