"""Audio de ida y vuelta con ElevenLabs real (criterio de hecho de T1-21).

No corre en CI (`-m 'not live'` por defecto). La clave se toma del `.env` de la raíz del repo.
Desde `backend/`:

    pytest -m live tests/test_voice_live.py -s

1. Una frase fija aprobada con cifras sale por `POST /voice/tts` como MP3 de ElevenLabs.
2. La misma frase, sintetizada en PCM 16 kHz, entra por `WS /voice/stt` y vuelve como texto.
"""

import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import API_PREFIX
from app.voice import elevenlabs, service

REPO_ENV = Path(__file__).resolve().parents[2] / ".env"
SENTENCE = "Te ha restado unos 470 € esta semana."
QUESTION = "¿Por qué ha bajado mi cartera esta semana?"
_CHUNK = 3200  # 100 ms de PCM 16 kHz mono 16 bits


def _settings() -> Settings | None:
    return Settings(_env_file=REPO_ENV) if REPO_ENV.is_file() else None


_SETTINGS = _settings()  # se lee al importar: `conftest.py` vacía la clave antes de cada test

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        _SETTINGS is None or not _SETTINGS.elevenlabs_api_key, reason="sin ELEVENLABS_API_KEY"
    ),
]


@pytest.fixture
def live(monkeypatch: pytest.MonkeyPatch) -> Iterator[elevenlabs.VoiceConfig]:
    assert _SETTINGS is not None
    monkeypatch.setenv("ELEVENLABS_API_KEY", _SETTINGS.elevenlabs_api_key)
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", _SETTINGS.elevenlabs_voice_id)
    monkeypatch.setenv("ELEVENLABS_TTS_MODEL", _SETTINGS.elevenlabs_tts_model)
    monkeypatch.setenv("ELEVENLABS_STT_MODEL", _SETTINGS.elevenlabs_stt_model)
    get_settings.cache_clear()
    service.reset()
    config = service._elevenlabs_config()
    assert config is not None
    yield config
    service.reset()


def test_tts_of_approved_sentence_is_real_mp3(
    client: TestClient, live: elevenlabs.VoiceConfig
) -> None:
    service.warm_up()
    service.register_approved("turn_live", 0, SENTENCE)
    start = time.perf_counter()
    with client.stream(
        "POST", f"{API_PREFIX}/voice/tts", json={"turn_id": "turn_live", "index": 0}
    ) as response:
        chunks = response.iter_bytes()
        first = next(chunks)
        first_byte_ms = (time.perf_counter() - start) * 1000
        audio = first + b"".join(chunks)
    print(f"\nTTS: {len(audio)} bytes, primer byte en {first_byte_ms:.0f} ms")
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert audio[:3] == b"ID3" or (audio[0] == 0xFF and audio[1] & 0xE0 == 0xE0)
    assert len(audio) > 5000


def test_stt_round_trip_of_fixed_sentence(client: TestClient, live: elevenlabs.VoiceConfig) -> None:
    pcm = b"".join(elevenlabs.synthesize(QUESTION, live, output_format="pcm_16000"))
    with client.websocket_connect(f"{API_PREFIX}/voice/stt") as ws:
        ws.send_json(
            {"type": "start", "sample_rate": 16000, "encoding": "pcm_s16le", "language": "es"}
        )
        for i in range(0, len(pcm), _CHUNK):
            ws.send_bytes(pcm[i : i + _CHUNK])
        start = time.perf_counter()
        ws.send_json({"type": "stop"})
        messages = []
        while True:
            message = ws.receive_json()
            messages.append(message)
            if message["type"] != "partial":
                break
    final_ms = (time.perf_counter() - start) * 1000
    print(
        f"\nSTT: {messages[-1]} ({len(messages) - 1} parciales, final {final_ms:.0f} ms tras stop)"
    )
    assert messages[-1]["type"] == "final"
    text = messages[-1]["text"].lower()
    assert "bajado" in text and "cartera" in text
