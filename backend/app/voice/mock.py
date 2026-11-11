"""Mock de voz (T0-06): sin ElevenLabs y sin red.

- STT: ignora el audio y devuelve siempre la misma pregunta (`SttPartialMessage` con el primer
  frame y `SttFinalMessage` al cerrar), sacadas de `schemas/examples/`.
- TTS: devuelve `data/voice/mock.mp3` sea cual sea la frase aprobada.
- Aviso de IA: `data/voice/disclaimer.mp3` si existe (T1-21); si no, el mismo `mock.mp3`.

Es el respaldo de `voice/service.py` sin clave de ElevenLabs (tests y CI): no se borra.
"""

from collections.abc import AsyncIterator, Iterator
from pathlib import Path

from app.schemas import examples
from app.schemas.voice import SttFinalMessage, SttPartialMessage, SttServerMessage

# backend/app/voice/mock.py → raíz del repo en local; en Docker /app/app/voice → / (data en /data).
DATA_VOICE_DIR = Path(__file__).resolve().parents[3] / "data" / "voice"
MOCK_MP3 = DATA_VOICE_DIR / "mock.mp3"
DISCLAIMER_MP3 = DATA_VOICE_DIR / "disclaimer.mp3"

_CHUNK = 16 * 1024


async def transcribe(audio: AsyncIterator[bytes]) -> AsyncIterator[SttServerMessage]:
    sent_partial = False
    async for _frame in audio:
        if not sent_partial:
            sent_partial = True
            yield SttPartialMessage.model_validate(examples.load("SttPartialMessage"))
    yield SttFinalMessage.model_validate(examples.load("SttFinalMessage"))


def _stream_file(path: Path) -> Iterator[bytes]:
    with path.open("rb") as f:
        while chunk := f.read(_CHUNK):
            yield chunk


def synthesize(_text: str) -> Iterator[bytes]:
    return _stream_file(MOCK_MP3)


def disclaimer() -> Iterator[bytes]:
    return _stream_file(DISCLAIMER_MP3 if DISCLAIMER_MP3.is_file() else MOCK_MP3)
