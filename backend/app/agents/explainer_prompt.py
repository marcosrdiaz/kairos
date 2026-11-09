"""Piezas del prompt del explicador: bloque de contexto (con caché), mensaje del usuario,
realimentación del reintento y parámetros de la llamada."""

import json
from typing import Any

from app.agents import claude, tools
from app.agents.context import Preloaded
from app.schemas.agents import AskChannel, AskRequest


def context_block(pre: Preloaded) -> str:
    """Contexto de la cartera para el prompt. Estable mientras dure la caché del contexto."""
    consensus = [
        {"event_id": e.event_id, "titulo": e.title, **e.surprise.model_dump(mode="json")}
        for e in pre.events
        if e.surprise.metric
    ]
    payload = {"contexto": pre.context.model_dump(mode="json"), "consenso_eventos": consensus}
    body = json.dumps(payload, ensure_ascii=False)
    return f"<contexto_cartera>\n{body}\n</contexto_cartera>"


def user_text(request: AskRequest, impact: bool) -> str:
    channel = "voz (máximo 3 frases)" if request.channel is AskChannel.VOICE else "texto"
    kind = "impacto: la cifra en euros va en la primera frase" if impact else "general"
    return (
        f"Canal: {channel}. Tipo de pregunta: {kind}.\n<pregunta>\n{request.question}\n</pregunta>"
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
            "respuesta al usuario, sin repetirlas."
        )
    else:
        text += "Escribe de nuevo la respuesta al usuario desde el principio."
    return text + (
        " No menciones esta corrección, no te disculpes, no des la razón a nadie y no comentes "
        "qué datos tienes. Usa solo cifras de los facts, copiando su `display`, y no des órdenes."
    )


def request_kwargs(messages: list[Any], pre: Preloaded, allow_tools: bool) -> dict[str, Any]:
    """Herramientas y `system` fijos delante (caché del prompt); la pregunta, detrás."""
    system = [
        {"type": "text", "text": claude.system_prompt()},
        {"type": "text", "text": context_block(pre), "cache_control": {"type": "ephemeral"}},
    ]
    return {
        **claude.base_kwargs(),
        "system": system,
        "tools": tools.DEFINITIONS,
        "tool_choice": {"type": "auto" if allow_tools else "none"},
        "messages": messages,
    }
