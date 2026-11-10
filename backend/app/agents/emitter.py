"""Paso de cada frase del explicador por el guardián antes de emitirla (D-010).

Una frase aprobada se convierte en `AskSentenceEvent` con los `calc_ids` que casó el guardián y
se registra en `voice` para que el TTS pueda leerla. Una frase con un marcador sin sustituir
(`<IMPORTE>`) cuenta como bloqueada aunque el guardián no vea cifras en ella, igual que una
frase meta: la que contesta a la corrección del reintento, habla del contexto o narra lo que va
a consultar ("tienes razón…", "según el contexto…", "voy a consultar…").
"""

import re
import time
from difflib import SequenceMatcher

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
_META = re.compile(
    r"\btienes razon\b|\b(?:disculpa\w*|perdon\w*|lo siento)\b|\bno vienen? de los datos\b"
    r"|\blos datos que tengo\b|\bsegun (?:el|mi) contexto\b"
    r"|\bel contexto (?:ya )?(?:tiene|incluye|dice)\b"
    r"|\b(?:voy a|necesito) (?:consultar|comparar|mirar|revisar)\b|\bconsulto\b|\bherramienta"
    r"|\bla instruccion\b|\bfrase anterior\b"
)
META_DETAIL = "habla de la conversación, del contexto o de las correcciones en vez de responder"

# Relleno que aparece al continuar tras un reintento ("Ya te he dado el reparto, así que completo
# con lo que falta"). No aporta nada: se descarta sin bloquear, para no gastar otro intento.
_FILLER = re.compile(
    r"\bya te he (?:dado|dicho|contado|explicado|comentado|resumido)\b"
    r"|\bcomo (?:te )?(?:decia|he dicho|comentaba|acabo de decir)\b"
    r"|\b(?:completo|continuo|sigo) con (?:lo que falta|el resto|la respuesta)\b"
    r"|\bpara completar (?:la respuesta|lo anterior)\b|\bretomando lo anterior\b"
)
# Una frase repite otra ya dicha si se parecen en orden (≥ 0,85) o si casi todas sus palabras
# están en la otra (≥ 0,85), con un mínimo de palabras para no confundir frases cortas.
_REPEAT_RATIO = 0.85
_REPEAT_MIN_WORDS = 6


def _comparable(text: str) -> str:
    """Sin acentos, mayúsculas ni puntuación: «La caída de NVIDIA…» ≈ «la caida de nvidia…»."""
    return " ".join(re.sub(r"[^\w\s]", " ", guardian.normalize(text)).split())


def repeats(text: str, said: str) -> bool:
    """Si `text` dice lo mismo que `said`, aunque cambie el orden («La caída de NVIDIA es la
    noticia que más…» tras «La noticia que más… es la caída de NVIDIA»)."""
    a, b = _comparable(text), _comparable(said)
    if SequenceMatcher(None, a, b).ratio() >= _REPEAT_RATIO:
        return True
    words_a, words_b = set(a.split()), set(b.split())
    shortest = min(len(words_a), len(words_b))
    if shortest < _REPEAT_MIN_WORDS:
        return False
    return len(words_a & words_b) / shortest >= _REPEAT_RATIO


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

    def skip_reason(self, text: str) -> str | None:
        """Por qué la frase se calla sin contar como bloqueo: repite una ya dicha (el modelo
        vuelve a empezar tras un reintento) o es relleno sobre la propia respuesta."""
        if any(repeats(text, said) for said in self.emitted):
            return "repite una frase ya dicha"
        if _FILLER.search(guardian.normalize(text)):
            return "relleno sobre la propia respuesta"
        return None

    def approve(self, text: str) -> AskSentenceEvent | str:
        """El evento de la frase si se aprueba; si no, el motivo."""
        if _PLACEHOLDER.search(text):
            return PLACEHOLDER_DETAIL
        if _META.search(guardian.normalize(text)):
            return META_DETAIL
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
