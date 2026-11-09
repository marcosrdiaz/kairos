"""Explicador: un turno de `/ask` (diseño del MVP §4.4, `SPEC.md` §9, D-010, D-011).

1. `meta` con el `turn_id` y si toca el aviso de IA.
2. Claude rápido, con el contexto precargado de la cartera en el prompt (con caché) y las
   herramientas de `tools.py`, escribe en streaming. El texto se parte en frases y cada una pasa
   por el guardián antes de emitirse como `sentence`; sus `calc_ids` son los que casó el guardián.
   Las frases aprobadas se registran en `voice` para el TTS.
3. Frase bloqueada → un reintento con el motivo. Si vuelve a bloquearse, o si no hay clave o la
   API falla, el resto sale de la plantilla (`fallback_used`), que también pasa el guardián.
4. `done` (o `error` si no se ha podido emitir ni una frase).
"""

import json
import time
from collections.abc import Generator, Iterator
from typing import Any
from uuid import uuid4

from app.agents import claude, context, guardian, templates, tools
from app.agents.context import Preloaded
from app.agents.fact_format import as_evidence
from app.agents.facts import move_facts
from app.agents.sentences import SentenceSplitter
from app.core.errors import AppError, ErrorCode
from app.impact import service as impact_service
from app.schemas.agents import (
    AskChannel,
    AskDoneEvent,
    AskErrorEvent,
    AskEvent,
    AskMetaEvent,
    AskRequest,
    AskSentenceEvent,
    Evidence,
    GuardianChannel,
    GuardianRequest,
)
from app.schemas.impact import MoveAttributionOut
from app.voice import service as voice_service

MAX_VOICE_SENTENCES = guardian.MAX_VOICE_SENTENCES
MAX_TEXT_SENTENCES = 5
MAX_TOOL_ROUNDS = 3
ATTEMPTS = 2
UNAVAILABLE = "El asistente no puede responder ahora mismo."

Stream = Generator[AskEvent, None, str | None]


class _Fallback(Exception):
    """El modelo no ha dado una respuesta utilizable: se pasa a la plantilla."""


def new_turn_id() -> str:
    return f"turn_{uuid4().hex}"


def context_block(pre: Preloaded) -> str:
    """Contexto de la cartera para el prompt. Estable mientras dure la caché del contexto."""
    consensus = [
        {"event_id": e.event_id, "titulo": e.title, **e.surprise.model_dump(mode="json")}
        for e in pre.events
        if e.surprise.metric
    ]
    payload = {"contexto": pre.context.model_dump(mode="json"), "consenso_eventos": consensus}
    return (
        "<contexto_cartera>\n" + json.dumps(payload, ensure_ascii=False) + "\n</contexto_cartera>"
    )


def _user_text(request: AskRequest, impact: bool) -> str:
    channel = "voz (máximo 3 frases)" if request.channel is AskChannel.VOICE else "texto"
    kind = "impacto: la cifra en euros va en la primera frase" if impact else "general"
    return (
        f"Canal: {channel}. Tipo de pregunta: {kind}.\n<pregunta>\n{request.question}\n</pregunta>"
    )


def _feedback(sentence: str, detail: str, said: list[str]) -> str:
    text = f"La frase «{sentence}» no ha pasado la revisión: {detail}. "
    if said:
        quoted = " ".join(f"«{s}»" for s in said)
        text += f"Ya se han dicho estas frases, no las repitas: {quoted}. Escribe solo cómo sigue."
    else:
        text += "Vuelve a escribir la respuesta entera."
    return text + " Usa solo cifras de los facts, copiando su `display`, y no des órdenes."


class Turn:
    def __init__(self, portfolio_id: str, request: AskRequest, disclaimer: bool) -> None:
        self.portfolio_id = portfolio_id
        self.request = request
        self.disclaimer = disclaimer
        self.turn_id = new_turn_id()
        self.topic = templates.topic(request.question)
        self.kind = templates.question_kind(self.topic)
        self.voice = request.channel is AskChannel.VOICE
        self.channel = GuardianChannel.VOICE if self.voice else GuardianChannel.TEXT
        self.emitted: list[str] = []
        self.evidence: list[Evidence] = []
        self.blocked_count = 0
        self.fallback_used = False
        self.first_sentence_ms = 0
        self._started = time.perf_counter()

    # --- Guardián ---

    def _full(self) -> bool:
        limit = MAX_VOICE_SENTENCES if self.voice else MAX_TEXT_SENTENCES
        return len(self.emitted) >= limit

    def _approve(self, text: str) -> AskSentenceEvent | str:
        """El evento de la frase si el guardián la aprueba; si no, el motivo."""
        index = len(self.emitted)
        request = GuardianRequest(
            text=text,
            channel=self.channel,
            question_kind=self.kind,
            sentence_index=index,
            evidence=self.evidence,
        )
        verdict = guardian.check(request)
        if not verdict.ok:
            return "; ".join(reason.detail for reason in verdict.reasons)
        calc_ids = list(
            dict.fromkeys(f.matched_calc_id for f in verdict.figures if f.matched_calc_id)
        )
        if not self.emitted:
            self.first_sentence_ms = int((time.perf_counter() - self._started) * 1000)
        self.emitted.append(text)
        voice_service.register_approved(self.turn_id, index, text)
        return AskSentenceEvent(
            type="sentence", turn_id=self.turn_id, index=index, text=text, calc_ids=calc_ids
        )

    # --- Modelo ---

    def _kwargs(self, client_messages: list[Any], pre: Preloaded, allow_tools: bool) -> Any:
        system = [
            {"type": "text", "text": claude.system_prompt()},
            {"type": "text", "text": context_block(pre), "cache_control": {"type": "ephemeral"}},
        ]
        return {
            **claude.base_kwargs(),
            "system": system,
            "tools": tools.DEFINITIONS,
            "tool_choice": {"type": "auto" if allow_tools else "none"},
            "messages": client_messages,
        }

    def _run_tools(self, final: Any) -> list[dict[str, Any]]:
        results = []
        for block in final.content:
            if getattr(block, "type", "") != "tool_use":
                continue
            result = tools.run(self.portfolio_id, block.name, block.input)
            self.evidence += as_evidence(result.facts)
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result.content,
                    "is_error": result.is_error,
                }
            )
        return results

    def _stream(self, client: Any, messages: list[Any], pre: Preloaded) -> Stream:
        """Una respuesta completa (con sus rondas de herramientas). Devuelve el motivo si una
        frase se bloquea; `None` si ha terminado bien."""
        for round_ in range(MAX_TOOL_ROUNDS + 1):
            splitter = SentenceSplitter()
            kwargs = self._kwargs(messages, pre, allow_tools=round_ < MAX_TOOL_ROUNDS)
            with client.messages.stream(**kwargs) as stream:
                for event in stream:
                    if getattr(event, "type", "") != "text":
                        continue
                    for sentence in splitter.feed(event.text):
                        outcome = self._approve(sentence)
                        if isinstance(outcome, str):
                            return _feedback(sentence, outcome, self.emitted)
                        yield outcome
                        if self._full():
                            return None
                final = stream.get_final_message()
            for sentence in splitter.flush():
                outcome = self._approve(sentence)
                if isinstance(outcome, str):
                    return _feedback(sentence, outcome, self.emitted)
                yield outcome
            if final.stop_reason == "refusal":
                raise _Fallback("rechazo")
            results = self._run_tools(final) if final.stop_reason == "tool_use" else []
            if not results:
                if not self.emitted:
                    raise _Fallback("respuesta vacía")
                return None
            if self._full():
                return None
            messages.append({"role": "assistant", "content": final.content})
            messages.append({"role": "user", "content": results})
        raise _Fallback("demasiadas rondas de herramientas")

    def _llm(self, client: Any, pre: Preloaded) -> Iterator[AskEvent]:
        impact = self.kind.value == "impact"
        messages: list[Any] = [
            {
                "role": "user",
                "content": [{"type": "text", "text": _user_text(self.request, impact)}],
            }
        ]
        for _ in range(ATTEMPTS):
            feedback = yield from self._stream(client, messages, pre)
            if feedback is None:
                return
            self.blocked_count += 1
            last = messages[-1]
            messages[-1] = {
                **last,
                "content": [*last["content"], {"type": "text", "text": feedback}],
            }
        raise _Fallback("bloqueada tras el reintento")

    # --- Plantilla ---

    def _move(self) -> MoveAttributionOut | None:
        if self.topic is not templates.Topic.MOVE:
            return None
        try:
            move = impact_service.explain_move(self.portfolio_id, "week")
        except AppError:
            return None
        self.evidence += as_evidence(move_facts(move))
        return move

    def _template(self, pre: Preloaded) -> Iterator[AskEvent]:
        self.fallback_used = True
        sentences = templates.answer(pre, self.request.question, self._move())
        for sentence in sentences[len(self.emitted) :]:
            if self._full():
                return
            outcome = self._approve(sentence)
            if not isinstance(outcome, str):
                yield outcome

    # --- Turno ---

    def events(self) -> Iterator[AskEvent]:
        yield AskMetaEvent(type="meta", turn_id=self.turn_id, disclaimer=self.disclaimer)
        try:
            pre = context.get(self.portfolio_id)
        except AppError as error:
            yield self._error(error.code.value, error.message)
            return
        self.evidence = pre.evidence()
        client = claude.get_client()
        try:
            if client is None:
                raise _Fallback("sin clave de Anthropic")
            yield from self._llm(client, pre)
        except _Fallback:
            yield from self._template(pre)
        except claude.UPSTREAM_ERRORS:
            yield from self._template(pre)
        if not self.emitted:
            yield self._error(ErrorCode.UPSTREAM_UNAVAILABLE.value, UNAVAILABLE)
            return
        yield AskDoneEvent(
            type="done",
            turn_id=self.turn_id,
            fallback_used=self.fallback_used,
            blocked_count=self.blocked_count,
            first_sentence_ms=self.first_sentence_ms,
        )

    def _error(self, code: str, message: str) -> AskErrorEvent:
        return AskErrorEvent(type="error", turn_id=self.turn_id, code=code, message=message)
