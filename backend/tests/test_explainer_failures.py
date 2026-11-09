"""Turno del explicador ante fallos: el stream SSE siempre acaba en `done` o en `error`.

Errores de transporte a mitad del stream, herramientas que fallan, respuestas cortadas por
`max_tokens`, marcadores sin sustituir, plazo del turno, demasiadas rondas de herramientas y
fallos inesperados del contexto o de la plantilla.
"""

from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

import httpx2
import pytest

from app.agents import claude, context, explainer, templates, tools
from app.config import get_settings
from app.impact import service as impact_service
from app.schemas.agents import AskChannel, AskRequest
from app.voice import service as voice_service
from tests.fakes import explainer as fx
from tests.fakes.claude_stream import FakeStreamingClaude, Reply

MOVE = "¿Por qué ha bajado?"
_REQUEST = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
_WEEK = fx.fact(fx.preloaded(), "change_week").display


@pytest.fixture(autouse=True)
def _clean(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    pre = fx.preloaded()
    monkeypatch.setattr(context, "get", lambda _pid: pre)
    monkeypatch.setattr(impact_service, "explain_move", lambda _pid, _period: fx.move())
    voice_service.reset()
    yield
    claude.set_client(None)
    voice_service.reset()


class _BrokenStream:
    """Stream que emite una frase y medio y luego falla como lo hace el transporte del SDK."""

    def __init__(self, error: Exception) -> None:
        self.error = error

    def __enter__(self) -> "_BrokenStream":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def __iter__(self) -> Iterator[SimpleNamespace]:
        yield SimpleNamespace(type="text", text=f"Esta semana tu cartera ha bajado {_WEEK}. Te ")
        raise self.error


def _broken_client(error: Exception) -> Any:
    return SimpleNamespace(messages=SimpleNamespace(stream=lambda **_: _BrokenStream(error)))


def _run(question: str = MOVE, channel: AskChannel = AskChannel.VOICE) -> list[dict[str, Any]]:
    request = AskRequest(question=question, channel=channel, session_id="ses_fail")
    turn = explainer.Turn("laura", request, disclaimer=False)
    return [event.model_dump(mode="json") for event in turn.events()]


def _sentences(events: list[dict[str, Any]]) -> list[str]:
    return [e["text"] for e in events if e["type"] == "sentence"]


@pytest.mark.parametrize(
    "error",
    [
        httpx2.ReadTimeout("timeout", request=_REQUEST),
        httpx2.RemoteProtocolError("peer closed connection"),
    ],
)
def test_transport_error_mid_stream_continues_with_template(error: Exception) -> None:
    claude.set_client(_broken_client(error))
    events = _run()
    assert events[-1]["type"] == "done"
    assert events[-1]["fallback_used"] is True
    texts = _sentences(events)
    assert texts[0] == f"Esta semana tu cartera ha bajado {_WEEK}."
    assert texts[1].startswith("La mayor parte viene de")
    assert [e["index"] for e in events if e["type"] == "sentence"] == [0, 1]


def test_unexpected_tool_error_is_a_tool_result(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(_pid: str, _args: Any) -> Any:
        raise KeyError("bug")

    monkeypatch.setitem(tools._HANDLERS, "get_exposure", boom)
    nvda = fx.fact(fx.preloaded(), "evt.nvda-2025-02.impact").display
    fake = FakeStreamingClaude(
        Reply("", tool_uses=[("get_exposure", {})]), Reply(f"Te ha restado unos {nvda}.")
    )
    claude.set_client(fake)
    events = _run()
    assert events[-1]["type"] == "done"
    assert events[-1]["fallback_used"] is False
    result = fake.messages.calls[1]["messages"][-1]["content"][0]
    assert result["is_error"] is True
    assert result["content"] == tools.TOOL_FAILED


def test_max_tokens_drops_the_cut_sentence() -> None:
    text = f"Esta semana tu cartera ha bajado {_WEEK}. Por las tecnol"
    claude.set_client(FakeStreamingClaude(Reply(text, stop_reason="max_tokens")))
    events = _run()
    assert _sentences(events) == [f"Esta semana tu cartera ha bajado {_WEEK}."]
    assert events[-1]["fallback_used"] is False


def test_max_tokens_without_sentences_uses_template() -> None:
    claude.set_client(
        FakeStreamingClaude(Reply("Esta semana tu cartera", stop_reason="max_tokens"))
    )
    events = _run()
    assert events[-1]["fallback_used"] is True
    assert _sentences(events)[0] == f"Esta semana tu cartera ha bajado {_WEEK}."


def test_placeholder_counts_as_blocked() -> None:
    total = fx.fact(fx.preloaded(), "total").display
    fake = FakeStreamingClaude(
        Reply("Tu cartera vale <IMPORTE>. Bien."), Reply(f"Tu cartera vale {total}.")
    )
    claude.set_client(fake)
    events = _run("Hola")
    assert _sentences(events) == [f"Tu cartera vale {total}."]
    assert events[-1]["blocked_count"] == 1
    assert "marcador" in fake.messages.calls[1]["messages"][-1]["content"][-1]["text"]


def test_markdown_list_does_not_waste_voice_sentences() -> None:
    claude.set_client(
        FakeStreamingClaude(Reply(f"Ha bajado {_WEEK}. 1. Por NVIDIA. 2. Por el BCE."))
    )
    events = _run()
    assert _sentences(events) == [f"Ha bajado {_WEEK}.", "Por NVIDIA.", "Por el BCE."]


def test_deadline_cuts_the_model_and_uses_template(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(explainer, "TURN_DEADLINE_S", -1.0)
    fake = FakeStreamingClaude(Reply(f"Esta semana tu cartera ha bajado {_WEEK}. Sigue."))
    claude.set_client(fake)
    events = _run()
    assert events[-1]["fallback_used"] is True
    assert len(fake.messages.calls) == 1
    assert _sentences(events)[0] == f"Esta semana tu cartera ha bajado {_WEEK}."


def test_too_many_tool_rounds_uses_template(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(impact_service, "list_event_impacts", lambda _pid, _days: fx.events())
    rounds = [Reply("", tool_uses=[("get_events", {"days": 7})])] * (explainer.MAX_TOOL_ROUNDS + 1)
    fake = FakeStreamingClaude(*rounds)
    claude.set_client(fake)
    events = _run()
    assert events[-1]["type"] == "done"
    assert events[-1]["fallback_used"] is True
    calls = fake.messages.calls
    assert len(calls) == explainer.MAX_TOOL_ROUNDS + 1
    assert calls[-1]["tool_choice"] == {"type": "none"}
    assert all(c["tool_choice"] == {"type": "auto"} for c in calls[:-1])


def test_unexpected_context_error_ends_with_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(_pid: str) -> Any:
        raise RuntimeError("bug")

    monkeypatch.setattr(context, "get", boom)
    events = _run()
    assert [e["type"] for e in events] == ["meta", "error"]
    assert events[1]["code"] == "UPSTREAM_UNAVAILABLE"


def test_unexpected_template_error_ends_with_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_: Any) -> Any:
        raise RuntimeError("bug")

    monkeypatch.setattr(templates, "answer", boom)
    events = _run()
    assert [e["type"] for e in events] == ["meta", "error"]
    assert events[1]["code"] == "UPSTREAM_UNAVAILABLE"


def test_usage_is_recorded_per_call() -> None:
    claude.set_client(FakeStreamingClaude(Reply(f"Esta semana tu cartera ha bajado {_WEEK}.")))
    request = AskRequest(question=MOVE, channel=AskChannel.VOICE, session_id="ses_usage")
    turn = explainer.Turn("laura", request, disclaimer=False)
    list(turn.events())
    assert turn.usage == [
        {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
        }
    ]


def test_haiku_runs_without_thinking(monkeypatch: pytest.MonkeyPatch) -> None:
    assert claude.base_kwargs()["thinking"] == {"type": "disabled"}
    monkeypatch.setenv("ANTHROPIC_MODEL_FAST", "claude-opus-5-5")
    get_settings.cache_clear()
    assert "thinking" not in claude.base_kwargs()
