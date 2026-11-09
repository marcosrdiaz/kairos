"""Textos cortos fuera de `/ask`: explicación de evento, frase del widget y aviso (§4.4).

Mismo esquema que el explicador: Claude rápido redacta con las cifras ya calculadas, el guardián
valida el texto entero con el canal que toca, un reintento con el motivo y, si no, la plantilla
(que también pasa el guardián). Sin clave de Anthropic, directamente la plantilla.
"""

import json
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


def _check(
    text: str, channel: GuardianChannel, kind: QuestionKind | None, evidence: list[Evidence]
) -> GuardianVerdict:
    request = GuardianRequest(
        text=text, channel=channel, question_kind=kind, sentence_index=0, evidence=evidence
    )
    return guardian.check(request)


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
        "system": claude.system_prompt(),
        "messages": [{"role": "user", "content": _message(task, found, feedback)}],
    }
    with client.messages.stream(**kwargs) as stream:
        return claude.final_text(stream.get_final_message())


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
    client = claude.get_client()
    feedback: str | None = None
    for _ in range(ATTEMPTS if client is not None else 0):
        try:
            text = _complete(client, task, found, feedback)
        except claude.UPSTREAM_ERRORS:
            break
        verdict = _check(text, channel, kind, evidence)
        if text and verdict.ok:
            return text, True
        feedback = "; ".join(r.detail for r in verdict.reasons) or "texto vacío"
    if _check(template, channel, kind, evidence).ok:
        return template, False
    return templates.SAFE_TEXT, False  # sin cifras ni órdenes: un test comprueba que pasa
