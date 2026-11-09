"""Voz con ElevenLabs (T1-21) sin red: el cliente HTTP y el WebSocket se sustituyen por fakes."""

import asyncio
import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import API_PREFIX
from app.schemas.voice import SttFinalMessage, SttPartialMessage, SttServerMessage
from app.voice import elevenlabs, service

TURN = "turn_el"
CONFIG = elevenlabs.VoiceConfig(api_key="k", voice_id="v", tts_model="tts", stt_model="stt")


@pytest.fixture(autouse=True)
def _empty_cache() -> Iterator[None]:
    service.reset()
    yield
    service.reset()


@pytest.fixture
def configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """Como si `.env` tuviera clave, voz y modelos (pero sin llamar a la red)."""
    for name, value in (
        ("ELEVENLABS_API_KEY", "k"),
        ("ELEVENLABS_VOICE_ID", "v"),
        ("ELEVENLABS_TTS_MODEL", "tts"),
        ("ELEVENLABS_STT_MODEL", "stt"),
    ):
        monkeypatch.setenv(name, value)
    get_settings.cache_clear()


# --- TTS ---


def test_tts_speaks_figures_in_words(
    client: TestClient, configured: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    spoken: list[str] = []

    def fake_synthesize(text: str, config: elevenlabs.VoiceConfig) -> Iterator[bytes]:
        spoken.append(text)
        return iter([b"ID3", b"audio"])

    monkeypatch.setattr(elevenlabs, "synthesize", fake_synthesize)
    service.register_approved(TURN, 0, "Te ha restado unos 470 € (un −1,4 %).")
    response = client.post(f"{API_PREFIX}/voice/tts", json={"turn_id": TURN, "index": 0})
    assert response.status_code == 200
    assert response.content == b"ID3audio"
    assert spoken == [
        "Te ha restado unos cuatrocientos setenta euros (un menos uno coma cuatro por ciento)."
    ]


def test_tts_upstream_failure_is_503(
    client: TestClient, configured: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    def failing(text: str, config: elevenlabs.VoiceConfig) -> Iterator[bytes]:
        raise elevenlabs.ElevenLabsError("caído")

    monkeypatch.setattr(elevenlabs, "synthesize", failing)
    service.register_approved(TURN, 0, "Frase.")
    response = client.post(f"{API_PREFIX}/voice/tts", json={"turn_id": TURN, "index": 0})
    assert response.status_code == 503
    assert response.json()["code"] == "UPSTREAM_UNAVAILABLE"


def test_unapproved_sentence_never_reaches_elevenlabs(
    client: TestClient, configured: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(text: str, config: elevenlabs.VoiceConfig) -> Iterator[bytes]:
        raise AssertionError("no debe llamar a ElevenLabs")

    monkeypatch.setattr(elevenlabs, "synthesize", forbidden)
    response = client.post(f"{API_PREFIX}/voice/tts", json={"turn_id": TURN, "index": 0})
    assert response.status_code == 404


def test_without_key_uses_mock_and_warm_up_is_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(text: str, config: elevenlabs.VoiceConfig) -> Iterator[bytes]:
        raise AssertionError("no debe llamar a ElevenLabs")

    monkeypatch.setattr(elevenlabs, "synthesize", forbidden)
    service.warm_up()
    service.register_approved(TURN, 0, "Frase.")
    from app.schemas.voice import TtsRequest

    assert b"".join(service.synthesize(TtsRequest(turn_id=TURN, index=0)))


def test_warm_up_never_raises(configured: None, monkeypatch: pytest.MonkeyPatch) -> None:
    def failing(text: str, config: elevenlabs.VoiceConfig) -> Iterator[bytes]:
        raise elevenlabs.ElevenLabsError("caído")

    monkeypatch.setattr(elevenlabs, "synthesize", failing)
    service.warm_up()


def test_disclaimer_is_the_pregenerated_file(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/voice/disclaimer")
    assert response.content == service.DISCLAIMER_MP3.read_bytes()


# --- STT: protocolo de Scribe v2 Realtime con un WebSocket falso ---


class FakeUpstream:
    def __init__(self, replies: list[dict[str, Any]]) -> None:
        self.sent: list[dict[str, Any]] = []
        self._replies = replies
        self._committed = asyncio.Event()
        self.closed = False

    async def send(self, message: str) -> None:
        payload = json.loads(message)
        self.sent.append(payload)
        if payload["commit"]:
            self._committed.set()

    async def recv(self) -> str:
        if not self._replies:
            await asyncio.sleep(3600)
        reply = self._replies.pop(0)
        if reply.get("message_type") == "committed_transcript":
            await self._committed.wait()  # Scribe solo confirma tras el `commit`
        return json.dumps(reply)

    async def close(self) -> None:
        self.closed = True


async def _frames(*frames: bytes) -> AsyncIterator[bytes]:
    for frame in frames:
        yield frame


def _run(
    upstream: FakeUpstream, monkeypatch: pytest.MonkeyPatch, *frames: bytes
) -> list[SttServerMessage]:
    async def fake_connect(url: str, **kwargs: Any) -> FakeUpstream:
        assert "model_id=stt" in url and "language_code=es" in url
        assert kwargs["additional_headers"] == {"xi-api-key": "k"}
        return upstream

    monkeypatch.setattr(elevenlabs, "connect", fake_connect)

    async def collect() -> list[SttServerMessage]:
        return [m async for m in elevenlabs.transcribe(_frames(*frames), CONFIG)]

    return asyncio.run(collect())


def test_stt_forwards_audio_and_commits(monkeypatch: pytest.MonkeyPatch) -> None:
    upstream = FakeUpstream([
        {"message_type": "session_started"},
        {"message_type": "partial_transcript", "text": "por qué"},
        {"message_type": "partial_transcript", "text": "por qué"},
        {"message_type": "partial_transcript", "text": ""},
        {"message_type": "committed_transcript", "text": "¿Por qué ha bajado?"},
    ])  # fmt: skip
    out = _run(upstream, monkeypatch, b"\x01\x00", b"\x02\x00")
    assert out == [SttPartialMessage(text="por qué"), SttFinalMessage(text="¿Por qué ha bajado?")]
    assert [m["commit"] for m in upstream.sent] == [False, False, True]
    assert upstream.sent[0]["audio_base_64"] == "AQA="
    assert upstream.sent[-1]["audio_base_64"] == ""
    assert upstream.closed


def test_stt_upstream_error_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    upstream = FakeUpstream([{"message_type": "auth_error", "error": "bad key"}])
    with pytest.raises(elevenlabs.ElevenLabsError, match="auth_error"):
        _run(upstream, monkeypatch, b"\x00\x00")
    assert upstream.closed


def test_stt_empty_transcript_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    upstream = FakeUpstream([{"message_type": "committed_transcript", "text": " "}])
    with pytest.raises(elevenlabs.ElevenLabsError, match="vacía"):
        _run(upstream, monkeypatch)


def test_stt_connection_failure_goes_to_plan_b(
    client: TestClient, configured: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def refused(url: str, **kwargs: Any) -> FakeUpstream:
        raise OSError("sin red")

    monkeypatch.setattr(elevenlabs, "connect", refused)
    with client.websocket_connect(f"{API_PREFIX}/voice/stt") as ws:
        ws.send_json(
            {"type": "start", "sample_rate": 16000, "encoding": "pcm_s16le", "language": "es"}
        )
        ws.send_json({"type": "stop"})
        message = ws.receive_json()
    assert message["type"] == "error"
    assert message["code"] == "UPSTREAM_UNAVAILABLE"


def test_stt_bad_client_message_mid_stream_is_validation_error(
    client: TestClient, configured: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    upstream = FakeUpstream([])

    async def fake_connect(url: str, **kwargs: Any) -> FakeUpstream:
        return upstream

    monkeypatch.setattr(elevenlabs, "connect", fake_connect)
    with client.websocket_connect(f"{API_PREFIX}/voice/stt") as ws:
        ws.send_json(
            {"type": "start", "sample_rate": 16000, "encoding": "pcm_s16le", "language": "es"}
        )
        ws.send_bytes(b"\x00\x00")
        ws.send_json({"type": "hola"})
        message = ws.receive_json()
    assert message["code"] == "VALIDATION_ERROR"
    assert upstream.closed
