"""Plantillas deterministas (`agents/templates.py`) y textos de widget, avisos y eventos
(`agents/service.py` → `writer.py`): todo pasa el guardián y `forbidden.yaml`."""

from collections.abc import Iterator
from decimal import Decimal
from typing import Any

import httpx2
import pytest

from app.agents import claude, context, guardian, service, templates, writer
from app.agents.fact_format import as_evidence, format_eur, format_fraction, money, text_evidence
from app.agents.facts import move_facts, status_facts, stub_facts
from app.schemas import examples
from app.schemas.agents import (
    EventImpactStub,
    ExplainerPlan,
    ExplanationStatus,
    GuardianChannel,
    GuardianRequest,
    QuestionKind,
    SentenceStatus,
    StatusFacts,
    StatusState,
)
from tests.fakes import explainer as fx
from tests.fakes.claude_stream import FakeStreamingClaude, Reply

QUESTIONS = ["¿Por qué ha bajado?", "¿Me afecta lo del BCE?", "¿Voy bien?", "Hola", "¿Y NVIDIA?"]


@pytest.fixture(autouse=True)
def _reset_client() -> Iterator[None]:
    yield
    claude.set_client(None)


def _assert_passes(text: str, evidence: Any, kind: QuestionKind | None, index: int = 0) -> None:
    request = GuardianRequest(
        text=text,
        channel=GuardianChannel.VOICE,
        question_kind=kind,
        sentence_index=index,
        evidence=evidence,
    )
    verdict = guardian.check(request)
    assert verdict.ok, (text, verdict.reasons)
    assert guardian.find_forbidden(text) == []


@pytest.mark.parametrize(
    ("question", "topic"),
    [
        ("¿Por qué ha bajado?", templates.Topic.MOVE),
        ("¿Por qué ha bajado esta semana?", templates.Topic.MOVE),
        ("¿Me afecta lo del BCE?", templates.Topic.EVENT),
        ("¿Cómo me afecta lo del petróleo?", templates.Topic.EVENT),
        ("¿Voy bien?", templates.Topic.PLAN),
        ("¿Llego a mi objetivo?", templates.Topic.PLAN),
        ("Hola", templates.Topic.GENERAL),
    ],
)
def test_topic(question: str, topic: templates.Topic) -> None:
    assert templates.topic(question) is topic


@pytest.mark.parametrize("question", QUESTIONS)
@pytest.mark.parametrize(
    "variant", ["full", "no_events", "no_projection", "off_track", "drift", "no_move"]
)
def test_answers_pass_guardian(question: str, variant: str) -> None:
    pre = fx.preloaded(
        with_events=variant != "no_events", with_projection=variant != "no_projection"
    )
    if variant == "off_track" and pre.projection is not None:
        projection = pre.projection.model_copy(update={"on_track": False, "gap_eur": Decimal(800)})
        pre = context.Preloaded(pre.context, pre.event_evidence, pre.events, projection)
        pre.context.facts.append(money("projection.gap", "gap", Decimal(800), projection.calc_id))
    if variant == "drift":
        plan = ExplainerPlan(on_track=True, goal_year=2040, drift_exceeded=True)
        pre = context.Preloaded(
            pre.context.model_copy(update={"plan": plan}),
            pre.event_evidence,
            pre.events,
            pre.projection,
        )
    move = None if variant == "no_move" else fx.move()
    evidence = pre.evidence() + as_evidence(move_facts(fx.move()))
    kind = templates.question_kind(templates.topic(question))
    sentences = templates.answer(pre, question, move)
    assert 1 <= len(sentences) <= 3
    for index, sentence in enumerate(sentences):
        _assert_passes(sentence, evidence, kind, index)


def test_event_template_picks_the_event_asked_about() -> None:
    events = fx.events()

    def matched(question: str) -> str | None:
        event = templates.match_event(events, question)
        return event.event_id if event else None

    assert matched("¿Me afecta lo del BCE?") == "bce-2025-06"
    assert matched("¿Y lo de NVIDIA?") == "nvda-2025-02"
    assert matched("¿Qué ha pasado?") == "nvda-2025-02"
    assert templates.match_event([], "¿BCE?") is None


def test_safe_text_has_no_figures_or_orders() -> None:
    for channel in GuardianChannel:
        request = GuardianRequest(
            text=templates.SAFE_TEXT,
            channel=channel,
            question_kind=None,
            sentence_index=0,
            evidence=[],
        )
        assert guardian.check(request).ok


# --- Textos de otros módulos ---


def _stub(name: str = "EventImpactOut") -> EventImpactStub:
    data = examples.load(name)
    return EventImpactStub.model_validate({k: data[k] for k in EventImpactStub.model_fields})


def _status(state: StatusState) -> StatusFacts:
    name = "StatusFacts.revisa_plan" if state is StatusState.REVISA_PLAN else "StatusFacts"
    return StatusFacts.model_validate(examples.load(name)).model_copy(update={"state": state})


@pytest.mark.parametrize("name", ["EventImpactOut", "EventImpactOut.nvda"])
def test_event_explanation_template_without_key(name: str) -> None:
    stub = _stub(name)
    text, status = service.write_event_explanation(stub)
    assert status is ExplanationStatus.TEMPLATE
    assert format_eur(stub.impact_eur) in text
    evidence = as_evidence(stub_facts(stub)) + text_evidence([stub.title], "event")
    for sentence in text.split(". "):
        _assert_passes(sentence, evidence, None, 1)


def test_event_explanation_by_model() -> None:
    stub = _stub()
    text = f"Poco: unos {format_eur(stub.impact_eur)} a tu favor por la bajada de tipos."
    claude.set_client(FakeStreamingClaude(Reply(text)))
    assert service.write_event_explanation(stub) == (text, ExplanationStatus.OK)


def test_event_explanation_retries_then_template() -> None:
    stub = _stub()
    fake = FakeStreamingClaude(Reply("Compra bonos ya."), Reply("Te afecta en 5.000 euros."))
    claude.set_client(fake)
    text, status = service.write_event_explanation(stub)
    assert status is ExplanationStatus.TEMPLATE
    assert text == templates.event_explanation(stub)
    assert "revisión" in fake.messages.calls[1]["messages"][0]["content"]


@pytest.mark.parametrize("state", list(StatusState))
def test_status_sentence_template(state: StatusState) -> None:
    facts = _status(state)
    text, status = service.write_status_sentence(facts)
    assert status is SentenceStatus.TEMPLATE
    assert text != templates.SAFE_TEXT
    evidence = as_evidence(status_facts(facts)) + text_evidence([facts.event_title], "event")
    request = GuardianRequest(
        text=text, channel=GuardianChannel.WIDGET, question_kind=None, sentence_index=0,
        evidence=evidence,
    )  # fmt: skip
    assert guardian.check(request).ok


def test_status_sentence_revisa_plan_mentions_both_weights() -> None:
    facts = _status(StatusState.REVISA_PLAN)
    text, _ = service.write_status_sentence(facts)
    assert facts.equity_current is not None and facts.equity_target is not None
    assert format_fraction(facts.equity_current) in text
    assert format_fraction(facts.equity_target) in text


def test_alert_message() -> None:
    stub = _stub("EventImpactOut.nvda")
    text = service.write_alert_message(stub)
    assert text == f"{stub.title}: tu cartera, unos {format_eur(stub.impact_eur)} menos."


@pytest.mark.parametrize(
    "outcome",
    [
        httpx2.ReadTimeout("timeout"),
        Reply("", stop_reason="refusal"),
        Reply(""),
        RuntimeError("bug inesperado"),  # tampoco puede romper el pipeline de eventos
    ],
)
def test_writer_failures_use_template(outcome: Any) -> None:
    claude.set_client(FakeStreamingClaude(outcome))
    stub = _stub()
    assert service.write_alert_message(stub) == templates.alert_message(stub)


def test_writer_uses_its_own_prompt_and_channel_task() -> None:
    stub = _stub("EventImpactOut.nvda")
    text = f"{stub.title}: unos {format_eur(stub.impact_eur)} menos."
    fake = FakeStreamingClaude(Reply(text))
    claude.set_client(fake)
    assert service.write_alert_message(stub) == text
    call = fake.messages.calls[0]
    assert call["system"] == claude.writer_prompt()
    assert "aviso al móvil" in call["messages"][0]["content"]


def test_widget_text_over_the_limit_is_retried_then_template() -> None:
    facts = _status(StatusState.ATENTO)
    assert facts.event_impact_eur is not None
    euros = format_eur(facts.event_impact_eur)
    long_text = (
        f"Hoy tu cartera tiene unos {euros} menos por el evento de las tecnológicas y eso se nota "
        "bastante en los fondos que tienes."
    )
    fake = FakeStreamingClaude(Reply(long_text), Reply("Una. Dos. Tres."))
    claude.set_client(fake)
    text, status = service.write_status_sentence(facts)
    assert status is SentenceStatus.TEMPLATE
    assert text == templates.status_sentence(facts)
    assert "palabras" in fake.messages.calls[1]["messages"][0]["content"]


@pytest.mark.parametrize(
    ("text", "channel", "fits"),
    [
        ("Todo en calma. Toca para ver por qué.", GuardianChannel.WIDGET, True),
        ("Una. Dos. Tres.", GuardianChannel.WIDGET, False),
        ("Una frase. Otra.", GuardianChannel.ALERT, False),
        (" ".join(["palabra"] * 30) + ".", GuardianChannel.ALERT, False),
        ("Una. Dos. Tres.", GuardianChannel.EVENT_EXPLANATION, True),
        ("Una. Dos. Tres. Cuatro.", GuardianChannel.TEXT, True),
    ],
)
def test_channel_limits(text: str, channel: GuardianChannel, fits: bool) -> None:
    assert (writer.too_long(text, channel) is None) is fits


def test_templates_fit_their_channel_limits() -> None:
    for name in ("EventImpactOut", "EventImpactOut.nvda"):
        stub = _stub(name)
        assert writer.too_long(templates.alert_message(stub), GuardianChannel.ALERT) is None
        explanation = templates.event_explanation(stub)
        assert writer.too_long(explanation, GuardianChannel.EVENT_EXPLANATION) is None
    for state in StatusState:
        text = templates.status_sentence(_status(state))
        assert writer.too_long(text, GuardianChannel.WIDGET) is None
