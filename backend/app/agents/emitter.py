"""Paso de cada frase del explicador por el guardián antes de emitirla (D-010).

Una frase aprobada se convierte en `AskSentenceEvent` con los `calc_ids` que casó el guardián y
se registra en `voice` para que el TTS pueda leerla. Una frase con un marcador sin sustituir
(`<IMPORTE>`) cuenta como bloqueada aunque el guardián no vea cifras en ella.
"""

import re
import time

from app.agents import guardian
from app.schemas.agents import (
    AskSentenceEvent,
    Evidence,
    GuardianChannel,
    GuardianRequest,
    QuestionKind,
)
from app.voice import service as voice_service

MAX_VOICE_SENTENCES = guardian.MAX_VOICE_SENTENCES
MAX_TEXT_SENTENCES = 5
_PLACEHOLDER = re.compile(r"<[^<>\n]{1,40}>")
PLACEHOLDER_DETAIL = "lleva un marcador sin sustituir; escribe el `display` del fact"


class Emitter:
    def __init__(
        self,
        turn_id: str,
        channel: GuardianChannel,
        kind: QuestionKind,
        evidence: list[Evidence],
        started: float,
    ) -> None:
        self.turn_id = turn_id
        self.channel = channel
        self.kind = kind
        self.evidence = evidence
        self.emitted: list[str] = []
        self.first_sentence_ms = 0
        self._started = started
        voice = channel is GuardianChannel.VOICE
        self._limit = MAX_VOICE_SENTENCES if voice else MAX_TEXT_SENTENCES

    @property
    def full(self) -> bool:
        return len(self.emitted) >= self._limit

    def approve(self, text: str) -> AskSentenceEvent | str:
        """El evento de la frase si se aprueba; si no, el motivo."""
        if _PLACEHOLDER.search(text):
            return PLACEHOLDER_DETAIL
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
        matched = (f.matched_calc_id for f in verdict.figures if f.matched_calc_id)
        if not self.emitted:
            self.first_sentence_ms = int((time.perf_counter() - self._started) * 1000)
        self.emitted.append(text)
        voice_service.register_approved(self.turn_id, index, text)
        return AskSentenceEvent(
            type="sentence",
            turn_id=self.turn_id,
            index=index,
            text=text,
            calc_ids=list(dict.fromkeys(matched)),
        )
