"""Cifras del guardián: formatos de número, tolerancias, valor absoluto, años y palabras."""

from decimal import Decimal

import pytest

from app.agents import guardian
from app.schemas.agents import Evidence, GuardianReasonCode
from tests.fakes.guardian import CALC_EUR, ev, req

UNKNOWN = GuardianReasonCode.UNKNOWN_FIGURE


def codes(text: str, *evidence: Evidence) -> list[GuardianReasonCode]:
    return [r.code for r in guardian.check(req(text, *evidence)).reasons]


# --- Un test por formato de número ---


@pytest.mark.parametrize(
    ("text", "value", "unit", "evidence"),
    [
        ("Tu patrimonio es de 1.295 euros.", "1295", "EUR", ev("1295.40")),
        ("Tu patrimonio es de 1295 euros.", "1295", "EUR", ev("1295.40")),
        ("Son 42.380,50 euros.", "42380.50", "EUR", ev("42380.50")),
        ("Te ha restado 470 €.", "470", "EUR", ev("-470.00")),
        ("Te ha restado 470€.", "470", "EUR", ev("-470.00")),
        ("Te ha restado 470 EUR.", "470", "EUR", ev("-470.00")),
        ("Subió 0,25 puntos.", "0.25", "pp", ev("0.0025", "fraction")),
        ("Recorte de 25 puntos básicos.", "25", "bp", ev("0.0025", "fraction")),
        ("Recorte de 25 pb.", "25", "bp", ev("0.0025", "fraction")),
        ("Tipos al 0,25 %.", "0.25", "percent", ev("0.0025", "fraction")),
        ("Un 61 % en bolsa.", "61", "percent", ev("0.61", "fraction")),
        ("Un 61% en bolsa.", "61", "percent", ev("0.61", "fraction")),
        ("Un 61 por ciento en bolsa.", "61", "percent", ev("0.61", "fraction")),
        ("Cayó un -4,5 %.", "-4.5", "percent", ev("-0.045", "fraction")),
        ("Cayó un −4,5 %.", "-4.5", "percent", ev("-0.045", "fraction")),
        ("Unos 42 mil euros.", "42000", "EUR", ev("42380.00")),
        ("Unos 1,2 millones de euros.", "1200000", "EUR", ev("1234567.00")),
        ("Llegarías en 2040.", "2040", "number", ev("2040", "year")),
        ("Te ha restado unos 470.", "470", "number", ev("-470.00")),
        ("Tienes 12,35 participaciones.", "12.35", "number", ev("12.34567", "units")),
        ("Con espacio duro: 470 euros.", "470", "EUR", ev("470.00")),
    ],
)
def test_number_formats(text: str, value: str, unit: str, evidence: Evidence) -> None:
    verdict = guardian.check(req(text, evidence))
    assert verdict.ok, verdict.reasons
    assert [(f.value, f.unit) for f in verdict.figures] == [(Decimal(value), unit)]


def test_figure_text_keeps_the_original_spelling() -> None:
    verdict = guardian.check(req("Son 1.295 Euros.", ev("1295")))
    assert verdict.figures[0].text == "1.295 Euros"


# --- Tolerancias ---


@pytest.mark.parametrize(
    ("shown", "evidence", "ok"),
    [
        ("101 euros", "100.00", True),  # el mayor de los dos: aquí ±1 €
        ("102 euros", "100.00", False),
        ("99 euros", "-100.00", True),
        ("472 euros", "470.00", True),  # aquí ±0,5 % (2,35 €)
        ("473 euros", "470.00", False),
        ("10.050 euros", "10000.00", True),  # ±50 €
        ("10.051 euros", "10000.00", False),
    ],
)
def test_eur_tolerance(shown: str, evidence: str, ok: bool) -> None:
    assert guardian.check(req(f"Son {shown}.", ev(evidence))).ok is ok


@pytest.mark.parametrize(
    ("shown", "ok"),
    [("76 %", True), ("76,5 %", True), ("75,5 %", True), ("76,6 %", False), ("75 %", False)],
)
def test_percent_tolerance_is_half_a_point(shown: str, ok: bool) -> None:
    assert guardian.check(req(f"Un {shown} en bolsa.", ev("0.76", "fraction"))).ok is ok


def test_basis_points_tolerance_is_half_a_basis_point() -> None:
    assert guardian.check(req("Recorte de 25 pb.", ev("0.0025", "fraction"))).ok
    assert not guardian.check(req("Recorte de 26 pb.", ev("0.0025", "fraction"))).ok


def test_rounding_of_what_is_written_also_counts() -> None:
    # "42 mil" redondea 42.380 (medio paso: 500 €), aunque supera ±0,5 %.
    assert guardian.check(req("Unos 42 mil euros.", ev("42380"))).ok
    assert not guardian.check(req("Unos 41 mil euros.", ev("42380"))).ok


def test_absolute_value_matches_negative_evidence() -> None:
    assert guardian.check(req("Te ha restado 470 euros.", ev("-470.00"))).ok
    assert guardian.check(req("Ha variado -470 euros.", ev("470.00"))).ok


def test_percent_does_not_match_euro_evidence() -> None:
    assert codes("Un 470 %.", ev("470.00")) == [UNKNOWN]


def test_unknown_figure_is_blocked_with_detail() -> None:
    verdict = guardian.check(req("Te ha restado unos 600 euros.", ev("-470.00", calc_id="c1")))
    assert not verdict.ok
    assert verdict.reasons[0].code == UNKNOWN
    assert "600 euros" in verdict.reasons[0].detail
    assert verdict.figures[0].matched_calc_id is None


def test_no_evidence_blocks_any_figure() -> None:
    assert codes("Son 470 euros.") == [UNKNOWN]


# --- matched_calc_id ---


def test_matched_calc_id_comes_from_the_closest_evidence() -> None:
    verdict = guardian.check(
        req("Son 470 euros.", ev("-469.80", calc_id="lejos"), ev("-470.00", calc_id=CALC_EUR))
    )
    assert verdict.figures[0].matched_calc_id == CALC_EUR


def test_evidence_with_calc_id_wins_a_tie() -> None:
    verdict = guardian.check(req("Son 470 euros.", ev("470"), ev("470", calc_id=CALC_EUR)))
    assert verdict.figures[0].matched_calc_id == CALC_EUR


def test_evidence_without_calc_id_still_validates() -> None:
    verdict = guardian.check(req("Tipos al 0,25 %.", ev("0.0025", "fraction")))
    assert verdict.ok
    assert verdict.figures[0].matched_calc_id is None


# --- Lo que no es cifra y los años ---


def test_small_integers_without_unit_are_not_figures() -> None:
    verdict = guardian.check(req("Tienes 3 fondos y 10 aportaciones."))
    assert verdict.ok
    assert verdict.figures == []


def test_small_integers_with_unit_are_figures() -> None:
    assert codes("Son 3 euros.") == [UNKNOWN]


def test_year_in_evidence_is_accepted() -> None:
    assert guardian.check(req("Llegarías a tu objetivo en 2040.", ev("2040", "year"))).ok


def test_year_not_in_evidence_is_unknown() -> None:
    assert codes("Llegarías a tu objetivo en 2038.", ev("2040", "year")) == [UNKNOWN]


def test_day_of_month_is_not_a_figure_but_the_year_is() -> None:
    assert guardian.check(req("El 12 de junio de 2025 bajó tipos.", ev("2025", "year"))).ok
    assert codes("El 12 de junio de 2025 bajó tipos.") == [UNKNOWN]


def test_time_of_day_is_not_a_figure() -> None:
    assert guardian.check(req("A las 18:00 habla el BCE.")).ok


@pytest.mark.parametrize("name", ["S&P 500", "IBEX 35", "Euro Stoxx 50", "Nasdaq-100"])
def test_index_names_are_not_figures(name: str) -> None:
    assert guardian.check(req(f"Tu fondo sigue al {name}.")).ok


def test_identifiers_with_digits_are_not_figures() -> None:
    assert guardian.check(req("El G20 y el covid19 no son cifras.")).ok


# --- Números en palabras ---


@pytest.mark.parametrize(
    "word", ["once", "veinte", "noventa", "cien", "doscientos", "mil", "un millón", "quinientas"]
)
def test_number_words_above_ten_are_unknown(word: str) -> None:
    assert UNKNOWN in codes(f"Te ha restado {word} euros.")


@pytest.mark.parametrize("word", ["uno", "dos", "tres", "diez", "miles", "cientos", "similar"])
def test_small_number_words_are_allowed(word: str) -> None:
    assert guardian.check(req(f"Hay {word} casos.")).ok


def test_multiplier_after_digits_is_not_a_number_word() -> None:
    assert guardian.check(req("Unos 42 mil euros.", ev("42380"))).ok
