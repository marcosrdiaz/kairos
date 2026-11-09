"""Cliente de ElevenLabs (D-043): TTS Flash v2.5 por HTTP y STT Scribe v2 Realtime por WebSocket.

La clave (`xi-api-key`) solo viaja del backend a ElevenLabs; nunca llega al navegador. Este
módulo no sabe nada de frases aprobadas ni de cifras: eso lo resuelve `service.py` antes.
"""

import asyncio
import base64
import json
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx
from websockets.asyncio.client import ClientConnection, connect

from app.schemas.voice import SttFinalMessage, SttPartialMessage, SttServerMessage

_API = "https://api.elevenlabs.io/v1"
_STT_URL = "wss://api.elevenlabs.io/v1/speech-to-text/realtime"
_SAMPLE_RATE = 16000
_TTS_FORMAT = "mp3_44100_128"
_TTS_TIMEOUT = httpx.Timeout(15.0, connect=5.0)
_STT_OPEN_TIMEOUT = 5.0
_STT_FINAL_TIMEOUT = 10.0  # tras el `stop`, cuánto esperamos la transcripción confirmada


class ElevenLabsError(Exception):
    """ElevenLabs no ha respondido como esperábamos (red, auth, cuota o transcripción vacía)."""


@dataclass(frozen=True)
class VoiceConfig:
    api_key: str
    voice_id: str
    tts_model: str
    stt_model: str
    language: str = "es"


_client: httpx.Client | None = None


def _http() -> httpx.Client:
    """Cliente compartido: reutiliza la conexión TLS entre frases (≈ 40 ms menos cada una)."""
    global _client
    if _client is None:
        _client = httpx.Client(base_url=_API, timeout=_TTS_TIMEOUT)
    return _client


# --- TTS ---


def synthesize(text: str, config: VoiceConfig, output_format: str = _TTS_FORMAT) -> Iterator[bytes]:
    """Audio de `text` en streaming. Abre la petición antes de devolver el iterador, así un fallo
    de ElevenLabs sale como `ElevenLabsError` y no como un MP3 vacío a medias."""
    request = _http().build_request(
        "POST",
        f"/text-to-speech/{config.voice_id}/stream",
        params={"output_format": output_format},
        headers={"xi-api-key": config.api_key},
        json={"text": text, "model_id": config.tts_model, "language_code": config.language},
    )
    try:
        response = _http().send(request, stream=True)
    except httpx.HTTPError as exc:
        raise ElevenLabsError(f"TTS sin respuesta: {exc!r}") from exc
    if response.status_code != 200:
        detail = response.read()[:300]
        response.close()
        raise ElevenLabsError(f"TTS respondió {response.status_code}: {detail!r}")
    return _iter_and_close(response)


def _iter_and_close(response: httpx.Response) -> Iterator[bytes]:
    try:
        yield from response.iter_bytes()
    finally:
        response.close()


# --- STT ---


def _stt_url(config: VoiceConfig) -> str:
    query = {
        "model_id": config.stt_model,
        "language_code": config.language,
        "audio_format": f"pcm_{_SAMPLE_RATE}",
        "commit_strategy": "manual",
    }
    return f"{_STT_URL}?{urlencode(query)}"


def _chunk(audio: bytes, *, commit: bool) -> str:
    return json.dumps({
        "message_type": "input_audio_chunk",
        "audio_base_64": base64.b64encode(audio).decode("ascii"),
        "commit": commit,
        "sample_rate": _SAMPLE_RATE,
    })  # fmt: skip


async def _send_audio(upstream: ClientConnection, audio: AsyncIterator[bytes]) -> None:
    """Reenvía los frames PCM y, al acabar (el cliente mandó `stop`), pide la transcripción."""
    async for frame in audio:
        await upstream.send(_chunk(frame, commit=False))
    await upstream.send(_chunk(b"", commit=True))


async def transcribe(
    audio: AsyncIterator[bytes], config: VoiceConfig
) -> AsyncIterator[SttServerMessage]:
    """`partial` mientras se habla y un `final` con la transcripción confirmada.

    Los errores del cliente (desconexión, mensaje no válido) salen tal cual del iterador de
    audio; los de ElevenLabs, como `ElevenLabsError`.
    """
    try:
        upstream = await connect(
            _stt_url(config),
            additional_headers={"xi-api-key": config.api_key},
            open_timeout=_STT_OPEN_TIMEOUT,
        )
    except Exception as exc:  # red, TLS, 401/403 en el handshake…
        raise ElevenLabsError(f"STT sin conexión: {exc!r}") from exc
    sender = asyncio.create_task(_send_audio(upstream, audio))
    receiving: asyncio.Task[str | bytes] | None = None
    last_partial = ""
    try:
        while True:
            if receiving is None:
                receiving = asyncio.ensure_future(upstream.recv())
            waits: set[asyncio.Future[object]] = {receiving}  # type: ignore[arg-type]
            if not sender.done():
                waits.add(sender)  # type: ignore[arg-type]
            timeout = None if not sender.done() else _STT_FINAL_TIMEOUT
            done, _ = await asyncio.wait(waits, timeout=timeout, return_when="FIRST_COMPLETED")
            if not done:
                raise ElevenLabsError("STT: no llegó la transcripción confirmada")
            if sender in done:
                sender.result()  # relanza desconexión o mensaje no válido del cliente
            if receiving not in done:
                continue
            message = json.loads(receiving.result())
            receiving = None
            kind = str(message.get("message_type", ""))
            text = str(message.get("text") or "").strip()
            if kind == "partial_transcript" and text and text != last_partial:
                last_partial = text
                yield SttPartialMessage(text=text)
            elif kind == "committed_transcript":
                if not text:
                    raise ElevenLabsError("STT: transcripción vacía")
                yield SttFinalMessage(text=text)
                return
            elif "error" in kind:
                raise ElevenLabsError(f"STT respondió {kind}: {message.get('error')!r}")
    finally:
        sender.cancel()
        if receiving is not None:
            receiving.cancel()
        await upstream.close()
