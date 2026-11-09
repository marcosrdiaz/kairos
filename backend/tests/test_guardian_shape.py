"""Forma del guardián (frases en voz, cifra en € en impacto) y ejemplos del contrato."""

import pytest

from app.agents import guardian
from app.schemas.agents import (
    GuardianChannel,
    GuardianReasonCode,
    GuardianRequest,
    GuardianVerdict,
    QuestionKind,
)
from app.schemas.examples import load
from tests.fakes.guardian import CALC_EUR, ev, req

VOICE = GuardianChannel.VOICE
IMPACT = QuestionKind.IMPACT


def codes(request: GuardianRequest) -> list[GuardianReasonCode]:
    return [r.code for r in guardian.check(request).reasons]


# --- TOO_LONG ---


@pytest.mark.parametrize(
    ("text", "count"),
    [
        ("Hola.", 1),
        ("Hola. Adiós.", 2),
        ("¿Qué tal? Bien. Gracias", 3),
        ("Las tecnológicas de EE. UU. caen tras resultados.", 1),
        ("Son 1.295 euros. Nada más.", 2),
        ("Uno... y otro.", 2),
    ],
)
def test_count_sentences(text: str, count: int) -> None:
    assert guardian.count_sentences(guardian.normalize(text)) == count


def test_three_sentences_in_voice_are_ok() -> None:
    request = req("Uno. Dos. Tres.", channel=VOICE, sentence_index=0)
    assert guardian.check(request).ok


def test_four_sentences_in_voice_are_too_long() -> None:
    request = req("Uno. Dos. Tres. Cuatro.", channel=VOICE, sentence_index=0)
    assert codes(request) == [GuardianReasonCode.TOO_LONG]


def test_streamed_fourth_sentence_is_too_long() -> None:
    assert guardian.check(req("Tres.", channel=VOICE, sentence_index=2)).ok
    assert codes(req("Cuatro.", channel=VOICE, sentence_index=3)) == [GuardianReasonCode.TOO_LONG]


@pytest.mark.parametrize(
    "channel",
    [
        GuardianChannel.TEXT,
        GuardianChannel.WIDGET,
        GuardianChannel.ALERT,
        GuardianChannel.EVENT_EXPLANATION,
    ],
)
def test_sentence_limit_only_applies_to_voice(channel: GuardianChannel) -> None:
    assert guardian.check(req("Uno. Dos. Tres. Cuatro.", channel=channel, sentence_index=0)).ok


# --- MISSING_EUR ---


def test_impact_first_sentence_without_eur_is_blocked() -> None:
    request = req("Tu cartera ha bajado algo.", question_kind=IMPACT, sentence_index=0)
    assert codes(request) == [GuardianReasonCode.MISSING_EUR]


def test_impact_first_sentence_with_eur_is_ok() -> None:
    request = req("Te ha restado 470 euros.", ev("-470"), question_kind=IMPACT, sentence_index=0)
    assert guardian.check(request).ok


def test_impact_unitless_figure_matching_eur_evidence_counts_as_eur() -> None:
    request = req("Te ha restado unos 470.", ev("-470"), question_kind=IMPACT, sentence_index=0)
    assert guardian.check(request).ok


def test_impact_percent_alone_is_not_enough() -> None:
    request = req(
        "Tu cartera ha bajado un 1 %.",
        ev("-0.01", "fraction"),
        question_kind=IMPACT,
        sentence_index=0,
    )
    assert codes(request) == [GuardianReasonCode.MISSING_EUR]


def test_impact_only_checks_the_first_sentence() -> None:
    assert guardian.check(req("Es por el BCE.", question_kind=IMPACT, sentence_index=1)).ok


@pytest.mark.parametrize("kind", [QuestionKind.GENERAL, None])
def test_general_questions_do_not_need_eur(kind: QuestionKind | None) -> None:
    assert guardian.check(req("Todo va según tu plan.", question_kind=kind, sentence_index=0)).ok


# --- Varios motivos y ejemplos del contrato ---


def test_reasons_accumulate() -> None:
    request = req(
        "Vende ya. Pierdes 600 euros. Uno. Dos.",
        question_kind=IMPACT,
        channel=VOICE,
        sentence_index=0,
    )
    found = set(codes(request))
    assert found == {
        GuardianReasonCode.FORBIDDEN_PATTERN,
        GuardianReasonCode.UNKNOWN_FIGURE,
        GuardianReasonCode.TOO_LONG,
    }


def test_contract_example_request_gives_contract_example_verdict() -> None:
    request = GuardianRequest.model_validate(load("GuardianRequest"))
    expected = GuardianVerdict.model_validate(load("GuardianVerdict"))
    assert guardian.check(request) == expected


def test_contract_blocked_example() -> None:
    request = GuardianRequest.model_validate(
        {**load("GuardianRequest"), "text": "Te ha restado unos 600 euros."}
    )
    verdict = guardian.check(request)
    blocked = GuardianVerdict.model_validate(load("GuardianVerdict.blocked"))
    assert verdict.ok is False
    assert verdict.reasons == blocked.reasons


def test_check_is_deterministic() -> None:
    request = req("Son 470 euros. Vende ya.", ev("470", calc_id=CALC_EUR))
    assert guardian.check(request) == guardian.check(request)
