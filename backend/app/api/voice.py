"""Endpoints de voz (diseño del MVP §4.5).

`WS /voice/stt`, `POST /voice/tts` (solo frases aprobadas) y `GET /voice/disclaimer`.
"""

import logging
import threading
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from app.core.errors import ErrorCode
from app.schemas.common import ErrorOut
from app.schemas.voice import SttErrorMessage, SttStartMessage, SttStopMessage, TtsRequest
from app.voice import service

logger = logging.getLogger(__name__)


def _warm_up_in_background() -> None:
    """Calienta la voz sin retrasar el arranque (la primera llamada puede tardar 7–11 s)."""
    threading.Thread(target=service.warm_up, name="voice-warm-up", daemon=True).start()


router = APIRouter(tags=["voice"], on_startup=[_warm_up_in_background])

_MP3: dict[int | str, dict[str, Any]] = {200: {"content": {"audio/mpeg": {}}}}
_TTS_RESPONSES: dict[int | str, dict[str, Any]] = {
    **_MP3,
    404: {"model": ErrorOut},
    422: {"model": ErrorOut},
}
_AUDIO_HEADERS = {"Cache-Control": "no-store"}


@router.post(
    "/voice/tts",
    response_class=StreamingResponse,
    responses=_TTS_RESPONSES,
)
def tts(body: TtsRequest) -> StreamingResponse:
    audio = service.synthesize(body)  # SENTENCE_NOT_APPROVED sale aquí, antes del stream
    return StreamingResponse(audio, media_type="audio/mpeg", headers=_AUDIO_HEADERS)


@router.get("/voice/disclaimer", response_class=StreamingResponse, responses=_MP3)
def disclaimer() -> StreamingResponse:
    return StreamingResponse(service.disclaimer(), media_type="audio/mpeg")


async def _send_error(ws: WebSocket, code: ErrorCode, message: str) -> None:
    error = SttErrorMessage(code=code.value, message=message)
    await ws.send_text(error.model_dump_json())


async def _audio_frames(ws: WebSocket) -> AsyncIterator[bytes]:
    """Frames binarios hasta `{"type": "stop"}` o hasta que el cliente se desconecte."""
    while True:
        message = await ws.receive()
        if message["type"] == "websocket.disconnect":
            raise WebSocketDisconnect(message.get("code", 1000))
        if message.get("bytes") is not None:
            yield message["bytes"]
        elif message.get("text") is not None:
            SttStopMessage.model_validate_json(message["text"])  # cualquier otro texto es error
            return


@router.websocket("/voice/stt")
async def stt(ws: WebSocket) -> None:
    await ws.accept()
    try:
        SttStartMessage.model_validate_json(await ws.receive_text())
        async for out in service.transcribe(_audio_frames(ws)):
            await ws.send_text(out.model_dump_json())
    except WebSocketDisconnect:
        return
    except ValidationError:
        await _send_error(ws, ErrorCode.VALIDATION_ERROR, "Mensaje no válido en el canal de voz.")
    except Exception:
        logger.exception("Fallo en la transcripción")
        await _send_error(
            ws,
            ErrorCode.UPSTREAM_UNAVAILABLE,
            "No se ha podido transcribir el audio. Prueba con una de las preguntas sugeridas.",
        )
    try:
        await ws.close()
    except (WebSocketDisconnect, RuntimeError):
        pass  # el cliente ya cerró al recibir el `final`: no es un error
