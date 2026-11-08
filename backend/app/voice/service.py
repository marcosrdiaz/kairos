"""Interfaz pública de voz (diseño del MVP §4.5, `SPEC.md` §10).

- `register_approved` lo llama `agents` con cada frase que el guardián aprueba. Es lo único que
  otros módulos importan de aquí.
- `synthesize` solo lee frases de esa caché (por turno, TTL 5 min): el cliente manda
  `turn_id` e `index`, nunca texto. Así la regla 3 (todo pasa por el guardián) cubre el audio.
- `transcribe`, `synthesize` y `disclaimer` delegan en `mock.py`; T1-21 los cambia a ElevenLabs
  sin cambiar su firma.
"""

from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock

from app.core import clock
from app.core.errors import AppError, ErrorCode
from app.schemas.voice import SttServerMessage, TtsRequest
from app.voice import mock

APPROVED_TTL = timedelta(minutes=5)


@dataclass(frozen=True)
class _Approved:
    text: str
    expires_at: datetime


_approved: dict[tuple[str, int], _Approved] = {}
_lock = Lock()


def _purge_expired(now: datetime) -> None:
    for key in [k for k, v in _approved.items() if v.expires_at <= now]:
        del _approved[key]


# --- Interfaz entre módulos ---


def register_approved(turn_id: str, index: int, text: str) -> None:
    """Guarda una frase ya aprobada por el guardián para poder sintetizarla durante 5 min."""
    now = clock.now()
    with _lock:
        _purge_expired(now)
        _approved[(turn_id, index)] = _Approved(text=text, expires_at=now + APPROVED_TTL)


def reset() -> None:
    """Vacía la caché de frases aprobadas (tests y `/demo/reset`)."""
    with _lock:
        _approved.clear()


# --- Lo usa `api/voice.py` ---


def get_approved(turn_id: str, index: int) -> str:
    """Texto aprobado de la frase o 404 `SENTENCE_NOT_APPROVED` si no existe o ha caducado."""
    now = clock.now()
    with _lock:
        _purge_expired(now)
        entry = _approved.get((turn_id, index))
    if entry is None:
        raise AppError(
            ErrorCode.SENTENCE_NOT_APPROVED,
            "Esa frase no está aprobada para leerla en voz alta.",
            details={"turn_id": turn_id, "index": index},
        )
    return entry.text


def synthesize(request: TtsRequest) -> Iterator[bytes]:
    """Audio MP3 de una frase aprobada. Comprueba la caché antes de abrir el stream."""
    text = get_approved(request.turn_id, request.index)
    return mock.synthesize(text)


def disclaimer() -> Iterator[bytes]:
    """Audio MP3 del aviso de IA: «Soy el asistente de KAIROS, una IA. No es asesoramiento…»."""
    return mock.disclaimer()


def transcribe(audio: AsyncIterator[bytes]) -> AsyncIterator[SttServerMessage]:
    """Transcribe el audio PCM 16 kHz del turno: mensajes `partial`, `final` o `error`."""
    return mock.transcribe(audio)
