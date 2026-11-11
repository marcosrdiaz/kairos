"""Piezas del prompt del explicador: bloque de contexto (con caché), mensaje del usuario,
realimentación del reintento y parámetros de la llamada.

Con varias carteras (T4-14), el bloque con caché lleva la lista de carteras y el contexto de la
elegida en la app; el contexto de las demás carteras de la pregunta va en el mensaje del usuario,
para no invalidar la caché del prompt en cada pregunta.
"""

import json
from typing import TYPE_CHECKING, Any

from app.agents import claude, tools
from app.agents.context import Preloaded
from app.agents.portfolio_scope import KIND_LABELS
from app.schemas.agents import AskChannel, AskRequest

if TYPE_CHECKING:
    from app.agents.ask_context import TurnData


def _contexto(pre: Preloaded) -> dict[str, Any]:
    consensus = [
        {"event_id": e.event_id, "titulo": e.title, **e.surprise.model_dump(mode="json")}
        for e in pre.events
        if e.surprise.metric
    ]
    contexto = pre.context.model_dump(mode="json")
    if not pre.has_plan:
        contexto["plan"] = None  # sin plan, `on_track` y `goal_year` serían inventados
    return {"contexto": contexto, "consenso_eventos": consensus}


def _carteras(data: "TurnData") -> list[dict[str, Any]]:
    return [
        {
            "portfolio_id": ref.id,
            "nombre": ref.name,
            "tipo": KIND_LABELS.get(ref.kind or "", None),
            "elegida_en_la_app": ref.id == data.focus,
        }
        for ref in data.refs
    ]


def context_block(pre: Preloaded | None, data: "TurnData | None" = None) -> str:
    """Contexto para el prompt. Estable mientras dure la caché del contexto de la cartera
    elegida y no cambie la lista de carteras."""
    payload: dict[str, Any] = _contexto(pre) if pre is not None else {"contexto": None}
    if data is not None and (len(data.refs) > 1 or data.focus is None):
        payload = {"carteras": _carteras(data), **payload}
    body = json.dumps(payload, ensure_ascii=False)
    return f"<contexto_cartera>\n{body}\n</contexto_cartera>"


def _others_block(data: "TurnData") -> str:
    others = [
        {"cartera": {"portfolio_id": pid, "nombre": data.scope.name(pid)}, **_contexto(pre)}
        for pid, pre in data.others.items()
    ]
    if not others:
        return ""
    body = json.dumps(others, ensure_ascii=False)
    return f"\n<contexto_otras_carteras>\n{body}\n</contexto_otras_carteras>"


def _targets_line(data: "TurnData") -> str:
    if len(data.refs) <= 1 and data.focus is not None:
        return ""
    if not data.targets:
        return "\nCarteras de la pregunta: no está claro; pregunta a cuál se refiere."
    names = ", ".join(f"«{data.scope.name(pid)}» ({pid})" for pid in data.targets)
    return f"\nCarteras de la pregunta: {names}."


def user_text(request: AskRequest, impact: bool, data: "TurnData | None" = None) -> str:
    channel = "voz (máximo 3 frases)" if request.channel is AskChannel.VOICE else "texto"
    kind = "impacto: la cifra en euros va en la primera frase" if impact else "general"
    extra = (_targets_line(data) + _others_block(data)) if data is not None else ""
    return (
        f"Canal: {channel}. Tipo de pregunta: {kind}.{extra}\n"
        f"<pregunta>\n{request.question}\n</pregunta>"
    )


def feedback(sentence: str, detail: str, said: list[str]) -> str:
    """Instrucción del sistema para el reintento. Va en un bloque de texto aparte y el usuario
    no la ve: el modelo no debe contestarla ni mencionarla."""
    text = (
        "[Instrucción interna del sistema, invisible para el usuario] "
        f"La frase «{sentence}» se ha descartado por: {detail}. "
    )
    if said:
        quoted = " ".join(f"«{s}»" for s in said)
        text += (
            f"El usuario ya ha oído estas frases: {quoted}. Escribe solo la continuación de la "
            "respuesta al usuario: no repitas ninguna, ni con otras palabras, y no digas que "
            "continúas ni que ya has dado una parte."
        )
    else:
        text += "Escribe de nuevo la respuesta al usuario desde el principio."
    return text + (
        " No menciones esta corrección, no te disculpes, no des la razón a nadie y no comentes "
        "qué datos tienes. Usa solo cifras de los facts, copiando su `display`, y no des órdenes."
    )


def request_kwargs(messages: list[Any], data: "TurnData", allow_tools: bool) -> dict[str, Any]:
    """Herramientas y `system` fijos delante (caché del prompt); la pregunta, detrás."""
    block = context_block(data.main, data)
    system = [
        {"type": "text", "text": claude.system_prompt()},
        {"type": "text", "text": block, "cache_control": {"type": "ephemeral"}},
    ]
    return {
        **claude.base_kwargs(),
        "system": system,
        "tools": tools.DEFINITIONS,
        "tool_choice": {"type": "auto" if allow_tools else "none"},
        "messages": messages,
    }
