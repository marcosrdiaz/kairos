"""Ejemplos y mocks de T0-05 (eventos, agentes, avisos).

La validación de cada ejemplo contra su modelo la hace `test_schema_examples.py`; aquí solo se
exige que existan los ejemplos de esta tarea y se prueban los validadores y los mocks.
"""

import json

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter, ValidationError

from app.main import API_PREFIX
from app.schemas import examples
from app.schemas.agents import AskEvent, AskMetaEvent, StatusFacts
from app.schemas.events import EventAnalysis, EventIn

REQUIRED_EXAMPLES = [
    "EventAnalysis",
    "ShockSet",
    "ReplayOut",
    "AskRequest",
    "AskMetaEvent",
    "AskSentenceEvent",
    "AskSentenceEvent.impact",
    "AskDoneEvent",
    "AskErrorEvent",
    "GuardianRequest",
    "GuardianVerdict",
    "GuardianVerdict.blocked",
    "ExplainerContext",
    "StatusFacts",
    "StatusFacts.revisa_plan",
    "AlertOut",
]


@pytest.mark.parametrize("name", REQUIRED_EXAMPLES)
def test_example_exists(name: str) -> None:
    assert any(p.stem == name for p in examples.example_files()), f"Falta examples/{name}.json"


# --- EventAnalysis: sin cifras ---


def _analysis(**changes: object) -> dict[str, object]:
    data = examples.load("EventAnalysis")
    data.update(changes)
    return data  # type: ignore[no-any-return]


def test_analysis_rejects_digits_in_chain() -> None:
    with pytest.raises(ValidationError, match="cifras"):
        EventAnalysis.model_validate(_analysis(causal_chain=["El BCE baja los tipos 0,25 puntos"]))


def test_analysis_rejects_digits_in_channel_text() -> None:
    data = _analysis()
    data["channels"][0]["rationale"] = "Bajan 25 puntos"  # type: ignore[index]
    with pytest.raises(ValidationError, match="cifras"):
        EventAnalysis.model_validate(data)


def test_analysis_rejects_digits_in_entity_name() -> None:
    data = _analysis()
    data["entities"][0]["name"] = "BCE 2025"  # type: ignore[index]
    with pytest.raises(ValidationError, match="cifras"):
        EventAnalysis.model_validate(data)


def test_analysis_allows_digits_in_identifiers() -> None:
    data = _analysis(event_id="bce-2025-06", analyzed_model="claude-sonnet-5-5")
    assert EventAnalysis.model_validate(data).event_id == "bce-2025-06"


def test_event_in_allows_title_with_digits_and_missing_observed() -> None:
    event = EventIn.model_validate(
        {
            "id": "bce-2025-06",
            "type": "central_bank",
            "title": "El BCE baja los tipos 0,25 puntos",
            "occurred_at": "2025-06-05T12:15:00Z",
            "text": "Texto del comunicado.",
            "source_urls": [],
            "consensus": None,
            "fallback_chain": ["El BCE baja los tipos"],
            "illustrative": True,
        }
    )
    assert event.observed is None


# --- Unión SSE ---


def test_sse_union_discriminates_by_type() -> None:
    adapter = TypeAdapter(AskEvent)
    assert isinstance(adapter.validate_python(examples.load("AskMetaEvent")), AskMetaEvent)
    with pytest.raises(ValidationError):
        adapter.validate_python({"type": "nope", "turn_id": "t"})


def test_status_facts_optionals_default_to_none() -> None:
    data = examples.load("StatusFacts.revisa_plan")
    for key in ("event_title", "top_asset_class", "main_channel", "event_impact_eur"):
        data.pop(key)
    assert StatusFacts.model_validate(data).event_impact_eur is None


# --- /ask: SSE de verdad ---


def _ask(client: TestClient, portfolio_id: str = "laura"):  # type: ignore[no-untyped-def]
    body = examples.load("AskRequest")
    return client.post(f"{API_PREFIX}/portfolios/{portfolio_id}/ask", json=body)


def test_ask_streams_event_stream_in_order(client: TestClient) -> None:
    response = _ask(client)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    frames = [f for f in response.text.split("\n\n") if f]
    assert all(f.startswith("data: ") for f in frames)
    events = [json.loads(f.removeprefix("data: ")) for f in frames]
    adapter = TypeAdapter(AskEvent)
    for event in events:
        adapter.validate_python(event)
    assert [e["type"] for e in events] == ["meta", "sentence", "sentence", "done"]
    assert [e["index"] for e in events if e["type"] == "sentence"] == [0, 1]


def test_ask_unknown_portfolio_is_json_404(client: TestClient) -> None:
    response = _ask(client, "nadie")
    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_ask_rejects_invalid_channel(client: TestClient) -> None:
    body = examples.load("AskRequest") | {"channel": "carrier-pigeon"}
    response = client.post(f"{API_PREFIX}/portfolios/laura/ask", json=body)
    assert response.status_code == 422


# --- /alerts y replay ---


def test_alerts_start_empty(client: TestClient) -> None:
    """Desde T2-08 son reales: sin eventos no hay avisos (los cubre `test_alerts_service.py`)."""
    response = client.get(f"{API_PREFIX}/portfolios/laura/alerts")
    assert response.status_code == 200
    assert response.json() == []


def test_alerts_unknown_portfolio(client: TestClient) -> None:
    assert client.get(f"{API_PREFIX}/portfolios/nadie/alerts").status_code == 404


def test_replay_mock_returns_trace_per_portfolio(client: TestClient) -> None:
    response = client.post(f"{API_PREFIX}/demo/replay/bce-2025-06")
    assert response.status_code == 200
    body = response.json()
    assert body["event_id"] == "bce-2025-06"
    assert set(body["portfolios"]) == {"laura", "javier"}
    assert all(v.startswith("calc_") for v in body["portfolios"].values())


def test_replay_disabled_outside_demo_mode(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.config import get_settings

    monkeypatch.setenv("DEMO_MODE", "false")
    get_settings.cache_clear()
    response = client.post(f"{API_PREFIX}/demo/replay/bce-2025-06")
    assert response.status_code == 403
    assert response.json()["code"] == "DEMO_MODE_DISABLED"
