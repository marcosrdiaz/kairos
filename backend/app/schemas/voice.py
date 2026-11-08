"""Contrato de voz (diseño del MVP §4.5).

- `WS /voice/stt`: el cliente manda `SttStartMessage`, frames binarios PCM y `SttStopMessage`;
  el servidor responde con `SttServerMessage` (`partial`, `final` o `error`).
- `POST /voice/tts`: `TtsRequest {turn_id, index}` → `audio/mpeg`. Solo frases aprobadas por el
  guardián (las registra `agents` con `voice.service.register_approved`); si no, 404
  `SENTENCE_NOT_APPROVED`. Nunca sintetiza texto libre del cliente (regla 3 de producto).
- `GET /voice/disclaimer`: `audio/mpeg` pregenerado con el aviso de IA.

Los mensajes del WebSocket no salen en el OpenAPI (FastAPI no documenta WebSockets): sus tipos
TS se escriben en `frontend/src/voice/` a partir de los ejemplos (`Stt*Message.json`).
"""

from typing import Annotated, Literal

from pydantic import Field

from app.schemas.common import ContractModel

# --- WS /voice/stt: cliente → servidor ---


class SttStartMessage(ContractModel):
    """Abre el turno de voz. Después llegan frames binarios PCM 16 kHz mono."""

    type: Literal["start"] = "start"
    sample_rate: Literal[16000] = 16000
    encoding: Literal["pcm_s16le"] = "pcm_s16le"
    language: Literal["es"] = "es"


class SttStopMessage(ContractModel):
    """El usuario suelta el botón: el servidor cierra el audio y responde con `final`."""

    type: Literal["stop"] = "stop"


SttClientMessage = Annotated[SttStartMessage | SttStopMessage, Field(discriminator="type")]

# --- WS /voice/stt: servidor → cliente ---


class SttPartialMessage(ContractModel):
    """Transcripción provisional mientras el usuario habla."""

    type: Literal["partial"] = "partial"
    text: str


class SttFinalMessage(ContractModel):
    """Transcripción final; el frontend la manda a `POST /portfolios/{id}/ask`."""

    type: Literal["final"] = "final"
    text: str


class SttErrorMessage(ContractModel):
    """Fallo del STT. El frontend pasa al plan B (preguntas sugeridas)."""

    type: Literal["error"] = "error"
    code: str  # uno de `core.errors.ErrorCode`, como en `ErrorOut`
    message: str


SttServerMessage = Annotated[
    SttPartialMessage | SttFinalMessage | SttErrorMessage, Field(discriminator="type")
]

# --- POST /voice/tts ---


class TtsRequest(ContractModel):
    """Frase aprobada a sintetizar: la `index` del turno `turn_id` del SSE de `/ask`."""

    turn_id: str = Field(min_length=1)
    index: int = Field(ge=0)
