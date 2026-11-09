"""Constructores de peticiones al guardián para los tests."""

from decimal import Decimal

from app.schemas.agents import Evidence, GuardianChannel, GuardianRequest, QuestionKind

CALC_EUR = "calc_eur"


def ev(value: str, unit: str = "EUR", calc_id: str | None = None) -> Evidence:
    return Evidence(
        value=Decimal(value), unit=unit, calc_id=calc_id, source=None if calc_id else "test"
    )


def req(
    text: str,
    *evidence: Evidence,
    channel: GuardianChannel = GuardianChannel.TEXT,
    question_kind: QuestionKind | None = None,
    sentence_index: int = 1,
) -> GuardianRequest:
    """Por defecto canal texto, sin tipo de pregunta y fuera de la primera frase: solo cifras."""
    return GuardianRequest(
        text=text,
        channel=channel,
        question_kind=question_kind,
        sentence_index=sentence_index,
        evidence=list(evidence),
    )
