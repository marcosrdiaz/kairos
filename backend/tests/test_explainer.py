"""Turno del explicador (`agents/explainer.py`) con FakeStreamingClaude y contexto fijo.

Cubre: frases validadas con `calc_ids`, reintento tras bloqueo, plantilla tras dos bloqueos, sin
clave o con la API caída, herramientas, límite de 3 frases en voz y registro para el TTS.
"""

import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import anthropic
import httpx2
import pytest

from app.agents import claude, context, explainer
from app.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.impact import service as impact_service
from app.planning import service as planning_service
from app.portfolio import service as portfolio_service
from app.schemas.agents import AskChannel, AskRequest
from app.voice import service as voice_service
from tests.fakes import explainer as fx
from tests.fakes.claude_stream import FakeStreamingClaude, Reply

MOVE = "¿Por qué ha bajado?"
EVENT = "¿Me afecta lo del BCE?"
PLAN = "¿Voy bien?"
_REQUEST = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


@pytest.fixture(autouse=True)
def _clean(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    pre = fx.preloaded()
    monkeypatch.setattr(context, "get", lambda _pid: pre)
    monkeypatch.setattr(impact_service, "explain_move", lambda _pid, _period: fx.move())
    voice_service.reset()
    yield
    claude.set_client(None)
    voice_service.reset()


def _install(*outcomes: Any) -> FakeStreamingClaude:
    fake = FakeStreamingClaude(*outcomes)
    claude.set_client(fake)
    return fake


def _run(question: str, channel: AskChannel = AskChannel.VOICE) -> list[dict[str, Any]]:
    request = AskRequest(question=question, channel=channel, session_id="ses_test")
    turn = explainer.Turn("laura", request, disclaimer=False)
    return [event.model_dump(mode="json") for event in turn.events()]


def _sentences(events: list[dict[str, Any]]) -> list[str]:
    return [e["text"] for e in events if e["type"] == "sentence"]


def _done(events: list[dict[str, Any]]) -> dict[str, Any]:
    assert events[0]["type"] == "meta"
    assert events[-1]["type"] == "done", events[-1]
    return events[-1]


def _display(key: str) -> str:
    return fx.fact(fx.preloaded(), key).display


def test_answer_streams_validated_sentences_with_calc_ids() -> None:
    week, nvda = _display("change_week"), _display("evt.nvda-2025-02.impact")
    text = (
        f"Esta semana tu cartera ha bajado {week}. Sobre todo por las tecnológicas de EE. UU., "
        f"que tras los resultados de NVIDIA te han restado unos {nvda}."
    )
    fake = _install(Reply(text))
    events = _run(MOVE)
    done = _done(events)
    sentences = [e for e in events if e["type"] == "sentence"]
    assert [s["index"] for s in sentences] == [0, 1]
    assert sentences[0]["calc_ids"] == [fx.portfolio().calc_id]
    assert sentences[1]["calc_ids"] == [fx.events()[0].calc_id]
    assert done["fallback_used"] is False
    assert done["blocked_count"] == 0
    assert done["first_sentence_ms"] >= 0
    turn_id = events[0]["turn_id"]
    assert voice_service.get_approved(turn_id, 1) == sentences[1]["text"]
    call = fake.messages.calls[0]
    assert call["model"] == get_settings().anthropic_model_fast
    assert call["system"][1]["cache_control"] == {"type": "ephemeral"}
    assert '"display"' in call["system"][1]["text"]


def test_blocked_sentence_is_retried_with_feedback() -> None:
    nvda = _display("evt.nvda-2025-02.impact")
    fake = _install(
        Reply("Te ha restado unos 600 euros. Otra frase."),
        Reply(f"Te ha restado unos {nvda} por los resultados de NVIDIA."),
    )
    events = _run(MOVE)
    done = _done(events)
    assert _sentences(events) == [f"Te ha restado unos {nvda} por los resultados de NVIDIA."]
    assert done["blocked_count"] == 1
    assert done["fallback_used"] is False
    retry = fake.messages.calls[1]["messages"][-1]["content"][-1]["text"]
    assert "600 euros" in retry
    assert "no está en las herramientas" in retry


def test_blocked_twice_falls_back_to_template() -> None:
    _install(Reply("Te recomiendo vender ya."), Reply("Te ha restado 999 euros."))
    events = _run(MOVE)
    done = _done(events)
    assert done["fallback_used"] is True
    assert done["blocked_count"] == 2
    sentences = [e for e in events if e["type"] == "sentence"]
    assert sentences[0]["text"].startswith("Esta semana tu cartera ha bajado 514 euros")
    assert all(s["calc_ids"] for s in sentences)


def test_template_continues_after_approved_sentences() -> None:
    week = _display("change_week")
    _install(
        Reply(f"Esta semana tu cartera ha bajado {week}. Te ha restado 999 euros."),
        Reply("Y además 888 euros."),
    )
    events = _run(MOVE)
    assert _done(events)["fallback_used"] is True
    texts = _sentences(events)
    assert texts[0] == f"Esta semana tu cartera ha bajado {week}."
    assert texts[1].startswith("La mayor parte viene de «NVIDIA")
    assert [e["index"] for e in events if e["type"] == "sentence"] == [0, 1]


def test_without_api_key_answers_with_template() -> None:
    events = _run(PLAN)
    done = _done(events)
    assert done["fallback_used"] is True
    assert done["blocked_count"] == 0
    assert _sentences(events)[0].endswith("150.000 euros en 2040.")


@pytest.mark.parametrize(
    "outcome",
    [
        anthropic.APIConnectionError(request=_REQUEST),
        anthropic.APITimeoutError(request=_REQUEST),
        anthropic.AnthropicError("caído"),
        Reply("", stop_reason="refusal"),
        Reply(""),
    ],
)
def test_upstream_failure_answers_with_template(outcome: Any) -> None:
    _install(outcome)
    events = _run(EVENT)
    assert _done(events)["fallback_used"] is True
    assert "0,25 puntos" in _sentences(events)[0]
    assert "90 euros a tu favor" in _sentences(events)[0]


def test_impact_question_needs_euros_in_first_sentence() -> None:
    bce = _display("evt.bce-2025-06.impact")
    fake = _install(
        Reply("Poco. Tus fondos de renta fija suben ligeramente."),
        Reply(f"Poco: unos {bce} a tu favor. Tus fondos de renta fija suben ligeramente."),
    )
    events = _run(EVENT, AskChannel.TEXT)
    assert _done(events)["blocked_count"] == 1
    assert _sentences(events)[0] == f"Poco: unos {bce} a tu favor."
    assert len(fake.messages.calls) == 2


def test_voice_answers_stop_at_three_sentences() -> None:
    week = _display("change_week")
    _install(Reply(f"Ha bajado {week}. Una. Dos. Tres. Cuatro."))
    events = _run(MOVE)
    assert len(_sentences(events)) == 3
    assert _done(events)["fallback_used"] is False


def test_tool_use_adds_tool_facts_as_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(context, "get", lambda _pid: fx.preloaded(with_projection=False))
    monkeypatch.setattr(portfolio_service, "get_plan", lambda _pid: fx.plan())
    monkeypatch.setattr(planning_service, "get_projection", lambda _pid: fx.projection())
    # 300 euros al mes solo sale de la proyección, que no está en el contexto de este test.
    answer = "Sí: con tus aportaciones de 300 euros al mes llegas a tu objetivo en 2040."
    fake = _install(Reply("", tool_uses=[("check_plan", {})]), Reply(answer))
    events = _run(PLAN)
    assert _done(events)["fallback_used"] is False
    sentence = next(e for e in events if e["type"] == "sentence")
    assert sentence["text"] == answer
    assert fx.projection().calc_id in sentence["calc_ids"]
    second = fake.messages.calls[1]["messages"]
    assert second[-1]["content"][0]["type"] == "tool_result"
    assert second[-1]["content"][0]["is_error"] is False


def test_context_error_ends_with_error_event(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(_pid: str) -> Any:
        raise AppError(ErrorCode.PRICE_UNAVAILABLE, "Sin precios.")

    monkeypatch.setattr(context, "get", fail)
    events = _run(MOVE)
    assert [e["type"] for e in events] == ["meta", "error"]
    assert events[1]["code"] == "PRICE_UNAVAILABLE"


def test_text_of_tool_use_rounds_is_dropped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(portfolio_service, "get_plan", lambda _pid: fx.plan())
    monkeypatch.setattr(planning_service, "get_projection", lambda _pid: fx.projection())
    week = _display("change_week")
    narration = f"Tu cartera ha bajado {week}. Para responder, consulto tu plan."
    answer = "Con tus aportaciones de 300 euros al mes llegas a tu objetivo en 2040. Bien."
    fake = _install(Reply(narration, tool_uses=[("check_plan", {})]), Reply(answer))
    events = _run(PLAN)
    assert _done(events)["fallback_used"] is False
    sentences = [e for e in events if e["type"] == "sentence"]
    assert [s["text"] for s in sentences] == [
        "Con tus aportaciones de 300 euros al mes llegas a tu objetivo en 2040.",
        "Bien.",
    ]
    assert [s["index"] for s in sentences] == [0, 1]
    turn_id = events[0]["turn_id"]
    assert voice_service.get_approved(turn_id, 0) == sentences[0]["text"]
    with pytest.raises(AppError):
        voice_service.get_approved(turn_id, 2)  # nada de la ronda descartada
    assert len(fake.messages.calls) == 2


def test_prompt_forbids_narrating_tool_calls() -> None:
    prompt = Path(claude.PROMPT_PATH).read_text(encoding="utf-8")
    assert "sin escribir nada antes" in prompt
    assert "usa la de la herramienta" in prompt


def test_prompt_has_no_example_figures() -> None:
    prompt = Path(claude.PROMPT_PATH).read_text(encoding="utf-8")
    assert "<IMPORTE>" in prompt
    assert not re.search(r"\d[\d.,]*\s*(?:€|euros?|%|por ciento)", prompt)
    assert not re.search(r"\b(?:19|20)\d{2}\b", prompt)
