"""Contrato y mock de voz (T0-06, diseño del MVP §4.5)."""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core import clock
from app.main import API_PREFIX
from app.schemas import examples
from app.voice import mock, service

TURN = "turn_test"


@pytest.fixture(autouse=True)
def _empty_cache() -> Iterator[None]:
    service.reset()
    yield
    service.reset()


# --- TTS: solo frases aprobadas ---


def test_tts_of_unapproved_sentence_is_404(client: TestClient) -> None:
    response = client.post(f"{API_PREFIX}/voice/tts", json={"turn_id": TURN, "index": 0})
    assert response.status_code == 404
    assert response.json() == {
        "code": "SENTENCE_NOT_APPROVED",
        "message": "Esa frase no está aprobada para leerla en voz alta.",
        "details": {"turn_id": TURN, "index": 0},
    }


def test_tts_of_approved_sentence_streams_mock_mp3(client: TestClient) -> None:
    service.register_approved(TURN, 0, "Frase aprobada por el guardián.")
    response = client.post(f"{API_PREFIX}/voice/tts", json={"turn_id": TURN, "index": 0})
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.content == mock.MOCK_MP3.read_bytes()


def test_tts_only_serves_the_approved_index(client: TestClient) -> None:
    service.register_approved(TURN, 0, "Primera frase.")
    response = client.post(f"{API_PREFIX}/voice/tts", json={"turn_id": TURN, "index": 1})
    assert response.status_code == 404


def test_tts_rejects_free_text_from_client(client: TestClient) -> None:
    body = {"turn_id": TURN, "index": 0, "text": "Compra ya."}
    response = client.post(f"{API_PREFIX}/voice/tts", json=body)
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_approved_sentence_expires_after_five_minutes() -> None:
    start = datetime(2026, 11, 8, 18, 0, tzinfo=UTC)
    clock.set_now(start)
    service.register_approved(TURN, 0, "Frase.")
    clock.set_now(start + timedelta(minutes=4, seconds=59))
    assert service.get_approved(TURN, 0) == "Frase."
    clock.set_now(start + timedelta(minutes=5))
    with pytest.raises(Exception, match="no está aprobada"):
        service.get_approved(TURN, 0)


def test_example_error_matches_service_error(client: TestClient) -> None:
    turn = examples.load("TtsRequest")
    response = client.post(f"{API_PREFIX}/voice/tts", json=turn)
    assert response.json() == examples.load("ErrorOut.sentence_not_approved")


# --- Aviso de IA ---


def test_disclaimer_is_mp3(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/voice/disclaimer")
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert len(response.content) > 1000


def test_mock_mp3_is_a_real_mp3() -> None:
    data = mock.MOCK_MP3.read_bytes()
    assert data[:3] == b"ID3" or (data[0] == 0xFF and data[1] & 0xE0 == 0xE0)


# --- STT por WebSocket ---


def test_stt_sends_partial_then_final(client: TestClient) -> None:
    with client.websocket_connect(f"{API_PREFIX}/voice/stt") as ws:
        ws.send_json(examples.load("SttStartMessage"))
        ws.send_bytes(b"\x00\x00" * 1600)
        assert ws.receive_json() == examples.load("SttPartialMessage")
        ws.send_bytes(b"\x00\x00" * 1600)
        ws.send_json(examples.load("SttStopMessage"))
        assert ws.receive_json() == examples.load("SttFinalMessage")


def test_stt_without_audio_still_sends_final(client: TestClient) -> None:
    with client.websocket_connect(f"{API_PREFIX}/voice/stt") as ws:
        ws.send_json(
            {"type": "start", "sample_rate": 16000, "encoding": "pcm_s16le", "language": "es"}
        )
        ws.send_json({"type": "stop"})
        assert ws.receive_json()["type"] == "final"


def test_stt_rejects_bad_start(client: TestClient) -> None:
    with client.websocket_connect(f"{API_PREFIX}/voice/stt") as ws:
        ws.send_json({"type": "start", "sample_rate": 44100})
        message = ws.receive_json()
    assert message["type"] == "error"
    assert message["code"] == "VALIDATION_ERROR"
