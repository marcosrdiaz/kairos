"""Frases que el explicador calla sin contar como bloqueo (T3-10): repeticiones de una frase ya
dicha (el modelo vuelve a empezar tras un reintento) y relleno sobre la propia respuesta.

Casos sacados de la evaluación de T3-01 (`tests/eval/resultados.md`: imp-09, trap-06, gen-07).
"""

from collections.abc import Iterator
from typing import Any

import pytest

from app.agents import claude, context, explainer, templates
from app.agents.emitter import Emitter, repeats
from app.agents.fact_format import as_evidence
from app.agents.facts import move_facts
from app.impact import service as impact_service
from app.schemas.agents import AskChannel, AskRequest, GuardianChannel, QuestionKind
from app.voice import service as voice_service
from tests.fakes import explainer as fx
from tests.fakes.claude_stream import FakeStreamingClaude, Reply

MOVE = "¿Por qué ha bajado?"
_WEEK = fx.fact(fx.preloaded(), "change_week").display
_NVDA = fx.fact(fx.preloaded(), "evt.nvda-2025-02.impact").display


@pytest.fixture(autouse=True)
def _clean(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    pre = fx.preloaded()
    monkeypatch.setattr(context, "get", lambda _pid: pre)
    monkeypatch.setattr(impact_service, "explain_move", lambda _pid, _period: fx.move())
    voice_service.reset()
    yield
    claude.set_client(None)
    voice_service.reset()


def _run(*replies: Reply) -> tuple[list[dict[str, Any]], FakeStreamingClaude]:
    fake = FakeStreamingClaude(*replies)
    claude.set_client(fake)
    request = AskRequest(question=MOVE, channel=AskChannel.TEXT, session_id="ses_clean")
    turn = explainer.Turn("laura", request, disclaimer=False)
    return [event.model_dump(mode="json") for event in turn.events()], fake


def _texts(events: list[dict[str, Any]]) -> list[str]:
    return [e["text"] for e in events if e["type"] == "sentence"]


def test_retry_that_starts_over_does_not_repeat_the_first_sentence() -> None:
    events, fake = _run(
        Reply(f"Esta semana tu cartera ha bajado {_WEEK}. Te ha restado 999 euros."),
        Reply(
            f"Tu cartera ha bajado {_WEEK} esta semana. Sobre todo por las tecnológicas de "
            f"EE. UU., que tras los resultados de NVIDIA te han restado unos {_NVDA}."
        ),
    )
    texts = _texts(events)
    assert texts == [
        f"Esta semana tu cartera ha bajado {_WEEK}.",
        f"Sobre todo por las tecnológicas de EE. UU., que tras los resultados de NVIDIA te han "
        f"restado unos {_NVDA}.",
    ]
    assert [e["index"] for e in events if e["type"] == "sentence"] == [0, 1]
    done = events[-1]
    assert done["type"] == "done"
    assert done["blocked_count"] == 1  # la repetición no cuenta como bloqueo
    assert done["fallback_used"] is False
    retry = fake.messages.calls[1]["messages"][-1]["content"][-1]["text"]
    assert "ni con otras palabras" in retry
    assert "no digas que continúas" in retry


def test_filler_after_retry_is_dropped_without_another_attempt() -> None:
    events, fake = _run(
        Reply(f"Esta semana tu cartera ha bajado {_WEEK}. Te ha restado 999 euros."),
        Reply(
            "Ya te he dado la cifra principal, así que completo con lo que falta. Sobre todo "
            f"por las tecnológicas de EE. UU., que te han restado unos {_NVDA}."
        ),
    )
    texts = _texts(events)
    assert len(texts) == 2
    assert not any("Ya te he dado" in t for t in texts)
    assert events[-1]["blocked_count"] == 1
    assert events[-1]["fallback_used"] is False
    assert len(fake.messages.calls) == 2


def test_a_whole_answer_of_repeats_falls_back_to_the_template() -> None:
    events, _ = _run(
        Reply(f"Esta semana tu cartera ha bajado {_WEEK}. Te ha restado 999 euros."),
        Reply(f"Tu cartera ha bajado {_WEEK} esta semana."),
    )
    texts = _texts(events)
    assert texts[0] == f"Esta semana tu cartera ha bajado {_WEEK}."
    assert len(texts) == len(set(texts))
    assert events[-1]["type"] == "done"


@pytest.mark.parametrize(
    ("text", "said"),
    [
        (  # imp-09: mismo contenido, otro orden
            "La caída de NVIDIA es la noticia que más ha movido tu cartera, con unos 89 euros "
            "en contra.",
            "La noticia que más ha movido tu cartera es la caída de NVIDIA, con un impacto "
            "estimado de unos 89 euros en contra.",
        ),
        (  # trap-06: idéntica
            "No puedo recomendarte que cambies tu cartera: KAIROS no da consejos de compra ni "
            "de venta.",
            "No puedo recomendarte que cambies tu cartera: KAIROS no da consejos de compra ni "
            "de venta.",
        ),
        (
            "Tu cartera ha bajado 658 euros esta semana.",
            "Esta semana tu cartera ha bajado 658 euros.",
        ),
    ],
)
def test_repeats_detects_the_same_sentence(text: str, said: str) -> None:
    assert repeats(text, said)


@pytest.mark.parametrize(
    ("text", "said"),
    [
        (
            "Tu parte directa en NVIDIA son unos 112 euros en contra.",
            "La caída de NVIDIA te resta unos 233 euros en total.",
        ),
        (
            "Incluso en el escenario pesimista llegarías a unos 137.040 euros.",
            "Vas bien: tu plan proyecta unos 169.324 euros en 2040 en el escenario base.",
        ),
        ("Vas bien.", "Vas bien con tu plan."),  # cortas: no se comparan por palabras
    ],
)
def test_repeats_lets_different_sentences_through(text: str, said: str) -> None:
    assert not repeats(text, said)


@pytest.mark.parametrize(
    "sentence",
    [
        "Ya te he dado el reparto principal, así que completo con lo que falta.",
        "Como te decía, la caída viene de NVIDIA.",
        "Para completar la respuesta, tu plan sigue en marcha.",
    ],
)
def test_filler_is_skipped(sentence: str) -> None:
    out = Emitter("turn_fill", GuardianChannel.TEXT, QuestionKind.GENERAL, [], 0.0)
    assert out.skip_reason(sentence) == "relleno sobre la propia respuesta"


@pytest.mark.parametrize(
    "sentence",
    [
        "Sigo tu plan: aportas cada mes.",
        "Te falta poco para tu objetivo.",
        "Lo que falta para tu objetivo depende de los mercados.",
    ],
)
def test_normal_sentences_are_not_filler(sentence: str) -> None:
    out = Emitter("turn_fill", GuardianChannel.TEXT, QuestionKind.GENERAL, [], 0.0)
    assert out.skip_reason(sentence) is None


@pytest.mark.parametrize(
    "question", ["¿Por qué ha bajado?", "¿Me afecta lo del BCE?", "¿Voy bien?"]
)
def test_template_sentences_are_never_skipped(question: str) -> None:
    pre = fx.preloaded()
    out = Emitter("turn_tpl", GuardianChannel.TEXT, QuestionKind.GENERAL, pre.evidence(), 0.0)
    out.evidence = pre.evidence() + as_evidence(move_facts(fx.move()))
    for sentence in templates.answer(pre, question, fx.move()):
        assert out.skip_reason(sentence) is None, sentence
        out.emitted.append(sentence)
