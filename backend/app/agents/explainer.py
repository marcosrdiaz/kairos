"""Explicador: un turno de `/ask` (diseño del MVP §4.4, `SPEC.md` §9, D-010, D-011).

1. `meta` con el `turn_id` y si toca el aviso de IA.
2. Claude rápido, con el contexto precargado de la cartera en el prompt (con caché) y las
   herramientas de `tools.py`, escribe en streaming. El texto se parte en frases y cada una pasa
   por el guardián (`emitter.py`) antes de emitirse como `sentence`.
3. Frase bloqueada → un reintento con el motivo. Si vuelve a bloquearse, si no hay clave, si la
   API falla (también a mitad del stream), si la respuesta llega cortada sin ninguna frase o si se
   agota el plazo del turno, el resto sale de la plantilla (`fallback_used`), que también pasa el
   guardián.
4. `done`, o `error` si no se ha podido emitir ni una frase. El stream nunca se corta sin uno de
   los dos: cualquier fallo inesperado se registra en el log.
"""

import logging
import time
from collections.abc import Generator, Iterator
from typing import Any
from uuid import uuid4

from app.agents import ask_context, claude, templates, tools
from app.agents import explainer_prompt as prompt
from app.agents.ask_context import TurnData
from app.agents.emitter import Emitter
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
    GuardianChannel,
    QuestionKind,
)
from app.schemas.impact import MoveAttributionOut

MAX_TOOL_ROUNDS = 3
ATTEMPTS = 2
TURN_DEADLINE_S = 6.0
"""Plazo de la parte del modelo; al superarlo se corta y sigue la plantilla."""
UNAVAILABLE = "El asistente no puede responder ahora mismo."

logger = logging.getLogger(__name__)
_monotonic = time.monotonic  # reloj del plazo; los tests lo sustituyen
_SENTENCE_END = (".", "!", "?", "…")
_CLOSERS = "»\"”')*_"

Stream = Generator[AskEvent, None, str | None]


class _Fallback(Exception):
    """El modelo no ha dado una respuesta utilizable: se pasa a la plantilla."""


def new_turn_id() -> str:
    return f"turn_{uuid4().hex}"


class Turn:
    """Un turno. `portfolio_id` es la cartera elegida en la app; `None` en `POST /ask` (T4-14):
    el asistente deduce de la pregunta por qué cartera o carteras pregunta."""

    def __init__(self, portfolio_id: str | None, request: AskRequest, disclaimer: bool) -> None:
        self.portfolio_id = portfolio_id
        self.request = request
        self.disclaimer = disclaimer
        self.turn_id = new_turn_id()
        self.topic = templates.topic(request.question)
        self.kind = templates.question_kind(self.topic)
        voice = request.channel is AskChannel.VOICE
        self.channel = GuardianChannel.VOICE if voice else GuardianChannel.TEXT
        self.blocked_count = 0
        self.fallback_used = False
        self.usage: list[dict[str, int]] = []
        self._started = time.perf_counter()
        self._deadline = 0.0  # se fija al empezar la parte del modelo (`_model_part`)
        self.out = Emitter(self.turn_id, self.channel, self.kind, [], self._started)
        self.data: TurnData | None = None  # se carga en `events`

    # --- Modelo ---

    def _check_deadline(self) -> None:
        if _monotonic() > self._deadline:
            raise _Fallback("plazo del turno agotado")

    def _record_usage(self, final: Any) -> None:
        usage = claude.usage_of(final)
        self.usage.append(usage)
        logger.info("Explicador %s: uso de Claude %s", self.turn_id, usage)

    def _run_tools(self, final: Any) -> list[dict[str, Any]]:
        results = []
        for block in final.content:
            if getattr(block, "type", "") != "tool_use":
                continue
            data = self._data()
            result = tools.run(data.default_portfolio, block.name, block.input, data.names)
            data.scope.add(result.portfolio_id, result.evidence())
            data.scope.add(None, result.shared)
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result.content,
                    "is_error": result.is_error,
                }
            )
        return results

    def _sentences(self, sentences: list[str]) -> Stream:
        for sentence in sentences:
            skip = self.out.skip_reason(sentence)
            if skip is not None:
                logger.info("Explicador %s: frase descartada (%s)", self.turn_id, skip)
                continue
            outcome = self.out.approve(sentence)
            if isinstance(outcome, str):
                return prompt.feedback(sentence, outcome, self.out.emitted)
            yield outcome
            if self.out.full:
                return None
        return None

    def _data(self) -> TurnData:
        assert self.data is not None, "los datos del turno se cargan en `events`"
        return self.data

    def _stream(self, client: Any, messages: list[Any], data: TurnData) -> Stream:
        """Una respuesta completa (con sus rondas de herramientas). Devuelve el motivo si una
        frase se bloquea; `None` si ha terminado bien.

        Las frases de cada ronda se retienen hasta conocer su `stop_reason`: el texto de una ronda
        que acaba llamando a herramientas («voy a consultar…», o una cifra que la herramienta
        puede corregir) nunca se emite."""
        for round_ in range(MAX_TOOL_ROUNDS + 1):
            splitter = SentenceSplitter()
            pending: list[str] = []
            kwargs = prompt.request_kwargs(messages, data, allow_tools=round_ < MAX_TOOL_ROUNDS)
            with client.messages.stream(**kwargs) as stream:
                for event in stream:
                    self._check_deadline()
                    if getattr(event, "type", "") == "text":
                        pending += splitter.feed(event.text)
                final = stream.get_final_message()
            self._record_usage(final)
            stop = final.stop_reason
            if stop == "refusal":
                raise _Fallback("rechazo del modelo")
            tail = splitter.flush()
            if stop == "max_tokens":  # la última frase, si está a medias, no se dice
                tail = [s for s in tail if s.rstrip(_CLOSERS).endswith(_SENTENCE_END)]
            pending += tail
            results = self._run_tools(final) if stop == "tool_use" else []
            if not results:
                blocked = yield from self._sentences(pending)
                if blocked is not None or self.out.full:
                    return blocked
                if not self.out.emitted:
                    raise _Fallback(f"respuesta sin frases ({stop})")
                return None
            if pending:
                logger.info("Explicador %s: texto antes de herramientas descartado", self.turn_id)
            messages.append({"role": "assistant", "content": final.content})
            messages.append({"role": "user", "content": results})
            self._check_deadline()
        raise _Fallback("demasiadas rondas de herramientas")

    def _llm(self, client: Any, data: TurnData) -> Iterator[AskEvent]:
        text = prompt.user_text(self.request, self.kind is QuestionKind.IMPACT, data)
        messages: list[Any] = [{"role": "user", "content": [{"type": "text", "text": text}]}]
        for _ in range(ATTEMPTS):
            feedback = yield from self._stream(client, messages, data)
            if feedback is None:
                return
            self.blocked_count += 1
            logger.info("Explicador %s: frase bloqueada: %s", self.turn_id, feedback)
            last = messages[-1]
            extra = {"type": "text", "text": feedback}
            messages[-1] = {**last, "content": [*last["content"], extra]}
        raise _Fallback("bloqueada tras el reintento")

    # --- Plantilla ---

    def _move(self, portfolio_id: str) -> MoveAttributionOut | None:
        if self.topic is not templates.Topic.MOVE:
            return None
        try:
            move = impact_service.explain_move(portfolio_id, "week")
        except AppError:
            return None
        self._data().scope.add(portfolio_id, as_evidence(move_facts(move)))
        return move

    def _template_sentences(self, data: TurnData) -> list[str]:
        if not data.targets:
            return ask_context.ambiguous_answer(data)
        if len(data.targets) > 1:
            return ask_context.portfolios_answer(data)
        target = data.targets[0]
        pre = data.preloaded(target)
        if pre is None:
            return ask_context.portfolios_answer(data)
        return templates.answer(pre, self.request.question, self._move(target))

    def _template(self, data: TurnData) -> Iterator[AskEvent]:
        """Sigue desde la frase siguiente a las ya dichas. `fallback_used` solo si la plantilla
        llega a emitir alguna frase."""
        sentences = self._template_sentences(data)
        for sentence in sentences[len(self.out.emitted) :]:
            if self.out.full:
                return
            outcome = self.out.approve(sentence)
            if not isinstance(outcome, str):
                self.fallback_used = True
                yield outcome

    # --- Turno ---

    def _model_part(self, data: TurnData) -> Iterator[AskEvent]:
        """La respuesta del modelo; si falla de cualquier forma, la plantilla."""
        self._deadline = _monotonic() + TURN_DEADLINE_S  # el contexto no cuenta
        client = claude.get_client()
        if client is None:
            logger.info("Explicador %s: sin clave de Anthropic, plantilla", self.turn_id)
        else:
            try:
                yield from self._llm(client, data)
                return
            except _Fallback as reason:
                logger.warning("Explicador %s: plantilla (%s)", self.turn_id, reason)
            except claude.UPSTREAM_ERRORS:
                logger.warning("Explicador %s: fallo de Claude", self.turn_id, exc_info=True)
            except Exception:
                logger.exception("Explicador %s: error inesperado del modelo", self.turn_id)
        yield from self._template(data)

    def events(self) -> Iterator[AskEvent]:
        yield AskMetaEvent(type="meta", turn_id=self.turn_id, disclaimer=self.disclaimer)
        try:
            data = self.data = ask_context.load(self.portfolio_id, self.request.question)
            self.out.scope = data.scope
            if not data.targets:  # pregunta a cuál se refiere: sin cifra en euros
                self.kind = self.out.kind = QuestionKind.GENERAL
            yield from self._model_part(data)
        except AppError as error:
            yield self._error(error.code.value, error.message)
            return
        except Exception:
            logger.exception("Explicador %s: error inesperado", self.turn_id)
            yield self._error(ErrorCode.UPSTREAM_UNAVAILABLE.value, UNAVAILABLE)
            return
        if not self.out.emitted:
            yield self._error(ErrorCode.UPSTREAM_UNAVAILABLE.value, UNAVAILABLE)
            return
        yield AskDoneEvent(
            type="done",
            turn_id=self.turn_id,
            fallback_used=self.fallback_used,
            blocked_count=self.blocked_count,
            first_sentence_ms=self.out.first_sentence_ms,
        )

    def _error(self, code: str, message: str) -> AskErrorEvent:
        return AskErrorEvent(type="error", turn_id=self.turn_id, code=code, message=message)
