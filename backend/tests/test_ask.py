"""`POST /portfolios/{id}/ask` de punta a punta: las 3 preguntas tipo con FakeStreamingClaude y
sin clave (plantilla), sobre la BD de prueba con el seed real.

El texto guionizado usa los `display` del contexto que construye la propia app, así que las
cifras salen siempre de los servicios, nunca del test.
"""

import json
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from app.agents import claude, context
from app.main import API_PREFIX
from app.schemas.agents import AskEvent
from app.voice import service as voice_service
from tests.fakes.claude_stream import FakeStreamingClaude, Reply

_ADAPTER: TypeAdapter[Any] = TypeAdapter(AskEvent)


@pytest.fixture(autouse=True)
def _clean() -> Iterator[None]:
    context.invalidate()
    voice_service.reset()
    yield
    claude.set_client(None)
    context.invalidate()
    voice_service.reset()


def _ask(
    client: TestClient, question: str, session: str = "ses_a", channel: str = "voice"
) -> list[dict[str, Any]]:
    body = {"question": question, "channel": channel, "session_id": session}
    response = client.post(f"{API_PREFIX}/portfolios/laura/ask", json=body)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    frames = [f for f in response.text.split("\n\n") if f]
    assert all(f.startswith("data: ") for f in frames)
    events = [json.loads(f.removeprefix("data: ")) for f in frames]
    for event in events:
        _ADAPTER.validate_python(event)
    return events


def _check_order(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    types = [e["type"] for e in events]
    assert types[0] == "meta" and types[-1] == "done", types
    assert set(types[1:-1]) == {"sentence"}
    assert len({e["turn_id"] for e in events}) == 1
    sentences = events[1:-1]
    assert [s["index"] for s in sentences] == list(range(len(sentences)))
    assert sentences[0]["calc_ids"], "la primera frase lleva una cifra trazable"
    return sentences


def _display(key: str) -> str:
    fact = context.get("laura").fact(key)
    assert fact is not None, key
    return fact.display


def _replay(client: TestClient, event_id: str) -> None:
    assert client.post(f"{API_PREFIX}/demo/replay/{event_id}").status_code == 200
    context.invalidate()


def test_why_did_it_drop(client: TestClient) -> None:
    week, total = _display("change_week"), _display("total")
    text = f"Esta semana tu cartera ha cambiado {week}. Ahora vale {total}."
    claude.set_client(FakeStreamingClaude(Reply(text)))
    sentences = _check_order(_ask(client, "¿Por qué ha bajado?"))
    assert [s["text"] for s in sentences] == text.replace(". ", ".|").split("|")
    assert all(s["calc_ids"] for s in sentences)


def test_how_does_the_ecb_affect_me(client: TestClient) -> None:
    _replay(client, "bce-2025-06")
    impact = _display("evt.bce-2025-06.impact")
    low, high = _display("evt.bce-2025-06.low"), _display("evt.bce-2025-06.high")
    text = (
        f"La bajada de tipos del BCE te afecta en unos {impact}. "
        f"La estimación va de {low} a {high}."
    )
    claude.set_client(FakeStreamingClaude(Reply(text)))
    events = _ask(client, "¿Me afecta lo del BCE?")
    sentences = _check_order(events)
    assert len(sentences) == 2
    assert events[-1]["fallback_used"] is False


def test_am_i_on_track(client: TestClient) -> None:
    goal, year = _display("projection.goal_amount"), _display("projection.goal_year")
    text = f"Vas en línea: en el escenario base llegas a tus {goal} en {year}."
    claude.set_client(FakeStreamingClaude(Reply(text)))
    sentences = _check_order(_ask(client, "¿Voy bien?", channel="text"))
    assert sentences[0]["text"] == text


@pytest.mark.parametrize(
    "question", ["¿Por qué ha bajado?", "¿Me afecta lo del BCE?", "¿Voy bien?"]
)
def test_without_key_answers_with_template(client: TestClient, question: str) -> None:
    _replay(client, "bce-2025-06")
    events = _ask(client, question)
    sentences = _check_order(events)
    assert 1 <= len(sentences) <= 3
    assert events[-1]["fallback_used"] is True
    turn_id = events[0]["turn_id"]
    assert voice_service.get_approved(turn_id, 0) == sentences[0]["text"]


def test_disclaimer_only_first_time_per_session(client: TestClient) -> None:
    first = _ask(client, "¿Voy bien?", session="ses_disclaimer")
    second = _ask(client, "¿Voy bien?", session="ses_disclaimer")
    other = _ask(client, "¿Voy bien?", session="ses_other")
    assert first[0]["disclaimer"] is True
    assert second[0]["disclaimer"] is False
    assert other[0]["disclaimer"] is True
    assert first[0]["turn_id"] != second[0]["turn_id"]


def test_unknown_portfolio_is_404_before_streaming(client: TestClient) -> None:
    body = {"question": "¿Voy bien?", "channel": "voice", "session_id": "ses_x"}
    response = client.post(f"{API_PREFIX}/portfolios/nadie/ask", json=body)
    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_context_is_cached_until_invalidated(client: TestClient) -> None:
    first = context.get("laura")
    assert context.get("laura") is first
    context.invalidate("laura")
    assert context.get("laura") is not first
