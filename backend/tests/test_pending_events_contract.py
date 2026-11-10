"""Contrato de los eventos pendientes de cierre: `GET /events/pending` (T4-04, D-089)."""

import re

from fastapi.testclient import TestClient

from app.main import API_PREFIX
from app.schemas import examples
from app.schemas.events import EventStatus, PendingEventOut

URL = f"{API_PREFIX}/events/pending"
FIGURE_FIELDS = {"impact_eur", "low_eur", "high_eur", "impact_pct", "calc_id", "breakdown"}


def test_example_is_valid_and_pending() -> None:
    event = PendingEventOut.model_validate(examples.load("PendingEventOut"))
    assert event.status is EventStatus.PENDING_CLOSE
    assert event.causal_chain


def test_pending_event_carries_no_figures() -> None:
    assert not FIGURE_FIELDS & set(PendingEventOut.model_fields)
    for line in PendingEventOut.model_validate(examples.load("PendingEventOut")).causal_chain:
        assert not re.search(r"\d", line), line


def test_route_lists_pending_events(client: TestClient) -> None:
    response = client.get(URL)

    assert response.status_code == 200
    [event] = response.json()
    assert event["status"] == "pending_close"
    assert event["causal_chain"]
    assert not FIGURE_FIELDS & set(event)


def test_route_is_in_the_openapi(client: TestClient) -> None:
    paths = client.app.openapi()["paths"]  # type: ignore[attr-defined]
    assert f"{API_PREFIX}/events/pending" in paths
