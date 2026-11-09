"""Interfaz pública de voz (diseño del MVP §4.5, `SPEC.md` §10).

- `register_approved` lo llama `agents` con cada frase que el guardián aprueba. Es lo único que
  otros módulos importan de aquí.
- `synthesize` solo lee frases de esa caché (por turno, TTL 5 min): el cliente manda
  `turn_id` e `index`, nunca texto. Así la regla 3 (todo pasa por el guardián) cubre el audio.
- `transcribe` y `synthesize` usan ElevenLabs (T1-21) si hay clave, voz y modelos en `.env`;
  si no, el mock (tests y CI, sin red). `warm_up` calienta la voz al arrancar el backend.
"""

import logging
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock

from app.config import get_settings
from app.core import clock
from app.core.errors import AppError, ErrorCode
from app.schemas.voice import SttServerMessage, TtsRequest
from app.voice import elevenlabs, mock, numbers

APPROVED_TTL = timedelta(minutes=5)
# backend/app/voice/service.py → raíz del repo en local; en Docker, /data (montado en Compose).
DISCLAIMER_MP3 = Path(__file__).resolve().parents[3] / "data" / "voice" / "disclaimer.mp3"
DISCLAIMER_TEXT = "Soy el asistente de KAIROS, una IA. No es asesoramiento financiero."
_FILE_CHUNK = 16 * 1024
logger = logging.getLogger(__name__)


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


def _elevenlabs_config() -> elevenlabs.VoiceConfig | None:
    """Config de ElevenLabs, o `None` si falta algo (tests y CI: se usa el mock, sin red)."""
    settings = get_settings()
    config = elevenlabs.VoiceConfig(
        api_key=settings.elevenlabs_api_key,
        voice_id=settings.elevenlabs_voice_id,
        tts_model=settings.elevenlabs_tts_model,
        stt_model=settings.elevenlabs_stt_model,
    )
    return (
        config
        if all((config.api_key, config.voice_id, config.tts_model, config.stt_model))
        else None
    )


def synthesize(request: TtsRequest) -> Iterator[bytes]:
    """Audio MP3 de una frase aprobada. Comprueba la caché antes de abrir el stream.

    Las cifras se pasan a palabras aquí, después del guardián y solo para el audio (D-043).
    Si ElevenLabs falla, 503 `UPSTREAM_UNAVAILABLE` y el frontend deja la respuesta en texto.
    """
    text = get_approved(request.turn_id, request.index)
    config = _elevenlabs_config()
    if config is None:
        return mock.synthesize(text)
    try:
        return elevenlabs.synthesize(numbers.spell_out(text), config)
    except elevenlabs.ElevenLabsError as exc:
        logger.warning("TTS no disponible: %s", exc)
        raise AppError(
            ErrorCode.UPSTREAM_UNAVAILABLE,
            "No se ha podido generar el audio. La respuesta sigue en texto.",
        ) from exc


def disclaimer() -> Iterator[bytes]:
    """Audio MP3 del aviso de IA: «Soy el asistente de KAIROS, una IA. No es asesoramiento…».
    Pregenerado con la voz de la app (`scripts/gen_disclaimer.py`): no gasta cuota ni espera."""
    if not DISCLAIMER_MP3.is_file():
        return mock.disclaimer()
    return _stream_file(DISCLAIMER_MP3)


def _stream_file(path: Path) -> Iterator[bytes]:
    with path.open("rb") as f:
        while chunk := f.read(_FILE_CHUNK):
            yield chunk


def transcribe(audio: AsyncIterator[bytes]) -> AsyncIterator[SttServerMessage]:
    """Transcribe el audio PCM 16 kHz del turno: mensajes `partial` y `final`. Si ElevenLabs
    falla, lanza una excepción y `api/voice.py` manda `error` `UPSTREAM_UNAVAILABLE`."""
    config = _elevenlabs_config()
    if config is None:
        return mock.transcribe(audio)
    return elevenlabs.transcribe(audio, config)


def warm_up() -> None:
    """Primera llamada a la voz para que no tarde 7–11 s en la demo (D-043). No falla nunca."""
    config = _elevenlabs_config()
    if config is None:
        return
    try:
        for _ in elevenlabs.synthesize("Hola.", config):
            pass
        logger.info("Voz de ElevenLabs calentada")
    except Exception as exc:  # el calentamiento nunca tumba el arranque
        logger.warning("No se ha podido calentar la voz: %s", exc)
