"""Cifras del guardián tras la revisión: sufijos pegados, monedas extranjeras, tolerancias
relativas en porcentajes, cifras sin unidad y no-cifras de la lista blanca."""

from decimal import Decimal

import pytest

from app.agents import guardian
from app.schemas.agents import GuardianChannel, GuardianReasonCode, QuestionKind
from tests.fakes.guardian import ev, req

EUR_470 = ev("-470.00", calc_id="calc_470")
RATE = ev("0.0025", "fraction")


# --- Cifras pegadas a letras y multiplicadores ---


@pytest.mark.parametrize(
    ("text", "value", "unit"),
    [
        ("Has perdido 600EUR.", "600", "EUR"),
        ("Has perdido 600e.", "600", "EUR"),
        ("Has perdido 600euros.", "600", "EUR"),
        ("Has perdido 5M€.", "5000000", "EUR"),
        ("Has perdido 1,2M€.", "1200000", "EUR"),
        ("Has perdido 470k.", "470000", "number"),
        ("Has perdido 470 k€.", "470000", "EUR"),
        ("Has perdido 3 mm de euros.", "3000000", "EUR"),
        ("Has perdido H600€.", "600", "EUR"),  # un código con unidad sí es cifra
    ],
)
def test_glued_figures_are_extracted_and_blocked(text: str, value: str, unit: str) -> None:
    verdict = guardian.check(req(text, EUR_470))
    assert not verdict.ok
    assert [(f.value, f.unit) for f in verdict.figures] == [(Decimal(value), unit)]


@pytest.mark.parametrize(
    "text", ["Te ha restado 470e.", "Te ha restado 0,47k€.", "€470", "EUR 470"]
)
def test_glued_and_prefixed_euros_match(text: str) -> None:
    verdict = guardian.check(req(text, EUR_470))
    assert verdict.ok, verdict.reasons
    assert verdict.figures[0].unit == "EUR"


@pytest.mark.parametrize("text", ["42 380 euros", "42 380 euros", "42 380 euros"])
def test_thousands_with_spaces_are_one_number(text: str) -> None:
    verdict = guardian.check(req(f"Tu cartera vale {text}.", ev("42380")))
    assert verdict.ok, verdict.reasons
    assert verdict.figures[0].value == Decimal(42380)


@pytest.mark.parametrize(
    "text",
    [
        "El G20 y el G7 se reúnen.",
        "Tras el covid19 y la covid-19.",
        "Resultados del T3 y del Q4.",
        "En el 1T2025 hubo resultados.",
        "El 2.º trimestre y el 3er trimestre.",
        "Tu fondo sigue al S&P 500.",
        "Tu fondo, el Vanguard U.S. 500 Stock Index Fund, sigue al índice.",
        "NVIDIA vendió menos chips H100 de lo esperado.",
        "Airbus entregó más A320 y el fondo X600 cayó.",
        "Tu Depósito a plazo 12 meses vence en enero.",
    ],
)
def test_whitelisted_names_are_not_figures(text: str) -> None:
    verdict = guardian.check(req(text, ev("2025", "year")))
    assert verdict.ok, verdict.reasons


# --- Tolerancia de porcentajes (desviación de SPEC §9: el menor de 0,5 pp y el 10 %) ---


@pytest.mark.parametrize(
    ("text", "ok"),
    [
        ("Bajó los tipos 0,25 %.", True),
        ("Bajó los tipos 0,3 %.", True),  # redondeo de lo escrito
        ("Bajó los tipos 0,27 %.", True),  # 10 % de 0,25 pp
        ("Bajó los tipos 0,28 %.", False),
        ("Bajó los tipos 0,7 %.", False),
        ("Bajó los tipos 0,75 %.", False),
        ("Subió los tipos 0,7 puntos.", False),
        ("Recorte de 25 pb.", True),
        ("Recorte de 75 pb.", False),
    ],
)
def test_small_rates_use_relative_tolerance(text: str, ok: bool) -> None:
    assert guardian.check(req(text, RATE)).ok is ok


def test_large_percentages_keep_half_a_point() -> None:
    share = ev("0.637", "fraction")
    assert guardian.check(req("Pesa un 64,1 %.", share)).ok
    assert not guardian.check(req("Pesa un 64,3 %.", share)).ok


# --- Cifras sin unidad: solo redondeo ---


def test_unitless_figure_only_allows_rounding() -> None:
    assert not guardian.check(req("Sube un 0,6.", RATE)).ok
    assert guardian.check(req("Sube un 0,25.", RATE)).ok
    assert guardian.check(req("Te ha restado unos 470.", EUR_470)).ok
    assert not guardian.check(req("Te ha restado unos 471.", EUR_470)).ok


# --- Monedas extranjeras ---


@pytest.mark.parametrize(
    ("text", "unit"),
    [("600 dólares", "USD"), ("600 $", "USD"), ("$600", "USD"), ("600 USD", "USD"),
     ("600 libras", "GBP"), ("£600", "GBP")],
)  # fmt: skip
def test_foreign_currency_is_its_own_unit(text: str, unit: str) -> None:
    verdict = guardian.check(req(f"Has perdido {text}.", ev("-600.00")))
    assert not verdict.ok
    assert verdict.figures[0].unit == unit


def test_foreign_currency_matches_its_own_or_unitless_evidence() -> None:
    assert guardian.check(req("Ha subido 600 dólares.", ev("600", "USD"))).ok
    assert guardian.check(req("Ha subido 600 dólares.", ev("600", ""))).ok
    assert not guardian.check(req("Ha subido 600 dólares.", ev("600", "GBP"))).ok


def test_foreign_currency_never_satisfies_missing_eur() -> None:
    request = req(
        "Ha bajado 470 dólares.", ev("470", "USD"), question_kind=QuestionKind.IMPACT,
        sentence_index=0,
    )  # fmt: skip
    assert [r.code for r in guardian.check(request).reasons] == [GuardianReasonCode.MISSING_EUR]


# --- Forma ---


def test_negative_sentence_index_counts_as_zero() -> None:
    request = req("Uno. Dos. Tres.", channel=GuardianChannel.VOICE, sentence_index=-1)
    assert guardian.check(request).ok
    request = req("Algo.", question_kind=QuestionKind.IMPACT, sentence_index=-1)
    assert [r.code for r in guardian.check(request).reasons] == [GuardianReasonCode.MISSING_EUR]
