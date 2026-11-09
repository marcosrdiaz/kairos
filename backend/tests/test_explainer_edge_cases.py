"""Casos límite del explicador y del redactor que salieron en la revisión de T1-17: plazo del
turno, respuesta cortada, `fallback_used`, impactos de 0 €, carteras sin plan, aviso de IA en voz,
cliente reutilizado, una sola llamada a `status` y plazo del redactor."""

from collections.abc import Iterator
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from app.agents import claude, context, explainer, service, templates, writer
from app.agents import explainer_prompt as prompt
from app.core.errors import AppError, ErrorCode
from app.impact import service as impact_service
from app.planning import service as planning_service
from app.portfolio import service as portfolio_service
from app.schemas import examples
from app.schemas.agents import AskChannel, AskRequest, EventImpactStub
from app.schemas.status import StatusOut
from app.status import service as status_service
from app.voice import service as voice_service
from tests.fakes import explainer as fx
from tests.fakes.claude_stream import FakeStreamingClaude, Reply

MOVE = "¿Por qué ha bajado?"
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


def _run(question: str = MOVE, channel: AskChannel = AskChannel.VOICE) -> list[dict[str, Any]]:
    request = AskRequest(question=question, channel=channel, session_id="ses_edge")
    turn = explainer.Turn("laura", request, disclaimer=False)
    return [event.model_dump(mode="json") for event in turn.events()]


def _sentences(events: list[dict[str, Any]]) -> list[str]:
    return [e["text"] for e in events if e["type"] == "sentence"]


# --- Explicador ---


def test_deadline_starts_with_the_model_not_with_the_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = {"now": 100.0}
    monkeypatch.setattr(explainer, "_monotonic", lambda: clock["now"])
    pre = fx.preloaded()

    def slow_context(_pid: str) -> context.Preloaded:
        clock["now"] += explainer.TURN_DEADLINE_S + 1  # contexto lento (caché vacía)
        return pre

    monkeypatch.setattr(context, "get", slow_context)
    claude.set_client(FakeStreamingClaude(Reply(f"Esta semana tu cartera ha bajado {_WEEK}.")))
    events = _run()
    assert events[-1]["fallback_used"] is False
    assert _sentences(events) == [f"Esta semana tu cartera ha bajado {_WEEK}."]


def test_max_tokens_keeps_a_finished_last_sentence() -> None:
    text = f"Esta semana tu cartera ha bajado {_WEEK}. Lo explica sobre todo NVIDIA."
    claude.set_client(FakeStreamingClaude(Reply(text, stop_reason="max_tokens")))
    events = _run()
    assert _sentences(events) == [
        f"Esta semana tu cartera ha bajado {_WEEK}.",
        "Lo explica sobre todo NVIDIA.",
    ]


def test_fallback_used_only_when_the_template_adds_a_sentence() -> None:
    first = f"Esta semana tu cartera ha bajado {_WEEK}."
    claude.set_client(
        FakeStreamingClaude(
            Reply(f"{first} Lo explica sobre todo NVIDIA. Te ha restado 999 euros."),
            Reply("Y además 888 euros."),
        )
    )
    events = _run(channel=AskChannel.TEXT)
    done = events[-1]
    assert done["type"] == "done"
    assert done["blocked_count"] == 2
    # La plantilla de movimiento tiene 2 frases y ya se han dicho 2: no añade nada.
    assert _sentences(events) == [first, "Lo explica sobre todo NVIDIA."]
    assert done["fallback_used"] is False


# --- Plantillas con impacto 0 ---


def test_zero_impact_is_not_read_as_a_gain() -> None:
    event = fx.events()[0].model_copy(
        update={"impact_eur": Decimal("0"), "low_eur": Decimal("-20"), "high_eur": Decimal("0")}
    )
    first = templates._event_sentences(event)[0]
    assert "0 euros a tu favor" not in first
    assert "a tu favor" not in first
    assert "20 euros en contra" in first


def test_zero_asset_change_is_not_read_as_more() -> None:
    move = fx.move()
    flat = [a.model_copy(update={"change_eur": Decimal("0")}) for a in move.by_asset]
    sentences = templates.answer(
        fx.preloaded(), MOVE, move.model_copy(update={"by_event": [], "by_asset": flat})
    )
    assert not any("0 euros más" in s for s in sentences)


# --- Contexto ---


def _services(monkeypatch: pytest.MonkeyPatch, calls: dict[str, int]) -> None:
    def missing(_pid: str) -> Any:
        raise AppError(ErrorCode.NOT_FOUND, "sin plan")

    def status(_pid: str) -> StatusOut:
        calls["status"] += 1
        return StatusOut.model_validate(examples.load("StatusOut"))

    monkeypatch.setattr(portfolio_service, "get_valued", lambda _pid: fx.portfolio())
    monkeypatch.setattr(portfolio_service, "get_plan", missing)
    monkeypatch.setattr(planning_service, "get_projection", missing)
    monkeypatch.setattr(impact_service, "list_event_impacts", lambda _pid, _days: [])
    monkeypatch.setattr(status_service, "get_status", status)


def test_without_plan_the_prompt_has_no_plan(monkeypatch: pytest.MonkeyPatch) -> None:
    _services(monkeypatch, {"status": 0})
    pre = context.build("laura")
    assert pre.has_plan is False
    block = prompt.context_block(pre)
    assert '"plan": null' in block
    assert '"on_track"' not in block


def test_with_plan_the_prompt_keeps_it() -> None:
    assert '"on_track": true' in prompt.context_block(fx.preloaded())


def test_cache_miss_reads_status_once(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"status": 0}
    _services(monkeypatch, calls)
    monkeypatch.undo()  # quita el `context.get` falso del fixture
    _services(monkeypatch, calls)
    context.invalidate()
    try:
        context.get("laura")
    finally:
        context.invalidate()
    assert calls["status"] == 1


# --- Aviso de IA ---


def test_disclaimer_again_when_the_session_starts_voice() -> None:
    service.reset_sessions()
    assert service.needs_disclaimer("ses_x", AskChannel.TEXT) is True
    assert service.needs_disclaimer("ses_x", AskChannel.TEXT) is False
    assert service.needs_disclaimer("ses_x", AskChannel.VOICE) is True
    assert service.needs_disclaimer("ses_x", AskChannel.VOICE) is False


def test_sessions_are_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    service.reset_sessions()
    monkeypatch.setattr(service, "MAX_SESSIONS", 3)
    for i in range(10):
        service.needs_disclaimer(f"ses_{i}", AskChannel.TEXT)
    assert len(service._sessions) == 3
    service.reset_sessions()


# --- Cliente ---


def test_client_is_reused(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = SimpleNamespace(anthropic_api_key="sk-test")
    monkeypatch.setattr(claude, "get_settings", lambda: settings)
    claude.set_client(None)
    assert claude.get_client() is claude.get_client()


# --- Redactor ---


def test_writer_deadline_uses_template(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(writer, "DEADLINE_S", -1.0)
    data = examples.load("EventImpactOut")
    impact = EventImpactStub.model_validate({k: data[k] for k in EventImpactStub.model_fields})
    fake = FakeStreamingClaude(Reply("Un texto cualquiera."), Reply("Otro texto."))
    claude.set_client(fake)
    assert service.write_alert_message(impact) == templates.alert_message(impact)
    assert len(fake.messages.calls) == 1
