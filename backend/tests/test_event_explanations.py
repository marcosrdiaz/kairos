"""Explicaciones de evento por cartera e invalidación del contexto precargado (T2-09)."""

import json
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.agents import claude, context
from app.agents import service as agents_service
from app.agents.explainer_prompt import context_block
from app.core import clock
from app.events import service
from app.main import API_PREFIX
from app.status import service as status_service
from tests.fakes.claude_stream import FakeStreamingClaude, Reply

NOW = datetime(2026, 11, 8, 18, 0, tzinfo=UTC)
EVENT_IDS = ("bce-2025-06", "oil-2025-06", "nvda-2025-02")
PORTFOLIO_IDS = ("laura", "javier")


class _QuotingMessages:
    """Redacta cada texto con la cifra real del impacto que le llega en `<facts>`."""

    def stream(self, **kwargs: Any) -> Any:
        content = kwargs["messages"][0]["content"]
        facts = json.loads(content.split("<facts>\n")[1].split("\n</facts>")[0])
        impact = next((f for f in facts if f["key"] == "impact"), None)
        text = f"Te afecta en unos {impact['display']}." if impact else "Tu cartera sigue igual."
        return FakeStreamingClaude(Reply(text)).messages.stream(**kwargs)


class _QuotingClaude:
    def __init__(self) -> None:
        self.messages = _QuotingMessages()


@pytest.fixture(autouse=True)
def _clean_state() -> Iterator[None]:
    clock.set_now(NOW)
    context.invalidate()
    yield
    claude.set_client(None)
    context.invalidate()


def _event_ids_in_context(portfolio_id: str) -> list[str]:
    return [e.event_id for e in agents_service.get_explainer_context(portfolio_id).events_7d]


@pytest.mark.parametrize("portfolio_id", PORTFOLIO_IDS)
@pytest.mark.parametrize("event_id", EVENT_IDS)
def test_replay_stores_a_model_explanation_for_each_portfolio(
    client: TestClient, event_id: str, portfolio_id: str
) -> None:
    claude.set_client(_QuotingClaude())
    client.post(f"{API_PREFIX}/demo/replay/{event_id}")
    event = client.get(f"{API_PREFIX}/portfolios/{portfolio_id}/events").json()[0]
    assert event["event_id"] == event_id
    assert event["explanation_status"] == "ok"
    assert event["explanation"].startswith("Te afecta en unos ")


@pytest.mark.parametrize("portfolio_id", PORTFOLIO_IDS)
def test_replay_refreshes_the_preloaded_context(client: TestClient, portfolio_id: str) -> None:
    assert _event_ids_in_context(portfolio_id) == []
    service.replay("oil-2025-06")
    assert _event_ids_in_context(portfolio_id) == ["oil-2025-06"]


def test_context_is_invalidated_after_recomputing_status(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, str | None]] = []
    real = status_service.recompute

    def recompute(portfolio_id: str) -> Any:
        calls.append(("recompute", portfolio_id))
        return real(portfolio_id)

    monkeypatch.setattr(status_service, "recompute", recompute)
    monkeypatch.setattr(
        agents_service, "invalidate_context", lambda p=None: calls.append(("invalidate", p))
    )
    service.replay("oil-2025-06")
    assert calls == [
        ("recompute", "laura"),
        ("invalidate", "laura"),
        ("recompute", "javier"),
        ("invalidate", "javier"),
        ("recompute", "victor"),
        ("invalidate", "victor"),
    ]


def test_prompt_block_is_stable_after_ttl_until_an_event_arrives(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D-071: sin cambios en los datos, el bloque no cambia y la caché del prompt sigue valiendo."""
    service.replay("oil-2025-06")
    elapsed = [0.0]
    monkeypatch.setattr(context, "_monotonic", lambda: elapsed[0])
    context.invalidate()
    before = context_block(context.get("laura"))
    elapsed[0] += context.TTL_S + 1
    clock.set_now(NOW + timedelta(seconds=61))
    assert context_block(context.get("laura")) == before
    service.replay("bce-2025-06")
    assert context_block(context.get("laura")) != before


def test_demo_reset_forgets_the_events_in_the_context(client: TestClient) -> None:
    service.replay("oil-2025-06")
    assert _event_ids_in_context("laura") == ["oil-2025-06"]
    client.post(f"{API_PREFIX}/demo/reset")
    assert _event_ids_in_context("laura") == []
