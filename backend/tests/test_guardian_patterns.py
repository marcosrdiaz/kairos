"""Patrones prohibidos del guardián: casos de cada patrón de `forbidden.yaml` y falsos positivos."""

import pytest

from app.agents import guardian
from app.schemas.agents import GuardianReasonCode
from tests.fakes.guardian import req

CONFIG = guardian.load_config()
PATTERNS = CONFIG.patterns
BLOCK_CASES = [(p.id, text) for p in PATTERNS for text in p.blocks]
ALLOW_CASES = [(p.id, text) for p in PATTERNS for text in p.allows]

# Lo que exige la SPEC (§9): debe bloquearse con algún patrón del fichero.
SPEC_EXAMPLES = [
    "Compra ya.",
    "Vende el fondo.",
    "No vendas.",
    "No compres más.",
    "Te recomiendo esperar.",
    "Deberías comprar bonos.",
    "Deberías vender bonos.",
    "Deberías invertir en Europa.",
    "Es buen momento para entrar.",
    "Invierte en renta fija.",
    "Sal de la tecnología.",
]

# Frases descriptivas del dominio que no deben bloquearse.
DESCRIPTIVE = [
    "Tu cartera ha bajado por la caída de las tecnológicas.",
    "Compraste el fondo en 2020 y lo mantienes.",
    "El precio medio de compra es menor que el actual.",
    "Tu aportación mensual compra más participaciones cuando el precio baja.",
    "La venta de deuda del banco central presiona los bonos.",
    "Vendiste parte de la posición el mes pasado.",
    "Según tu plan, tu aportación de este mes sigue en marcha.",
    "Tu asignación se ha alejado del objetivo de tu plan: revisa tu plan.",
    "Las tecnológicas de EE. UU. caen tras resultados.",
    "El fondo invierte sobre todo en Europa.",
    "Los inversores aprovecharon la subida.",
    "Esto no es asesoramiento financiero.",
]


def test_every_pattern_has_a_blocking_example() -> None:
    missing = [p.id for p in PATTERNS if not p.blocks]
    assert not missing, f"Patrones sin ejemplo en `blocks`: {missing}"


def test_pattern_ids_are_unique() -> None:
    ids = [p.id for p in PATTERNS]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize(("pattern_id", "text"), BLOCK_CASES)
def test_pattern_blocks_its_examples(pattern_id: str, text: str) -> None:
    assert pattern_id in [hit for hit, _ in guardian.find_forbidden(text)]
    verdict = guardian.check(req(text))
    assert not verdict.ok
    assert GuardianReasonCode.FORBIDDEN_PATTERN in [r.code for r in verdict.reasons]


@pytest.mark.parametrize(("pattern_id", "text"), ALLOW_CASES)
def test_pattern_allows_descriptive_examples(pattern_id: str, text: str) -> None:
    assert guardian.find_forbidden(text) == [], pattern_id


@pytest.mark.parametrize("text", SPEC_EXAMPLES)
def test_spec_patterns_are_covered(text: str) -> None:
    assert guardian.find_forbidden(text)


@pytest.mark.parametrize("text", DESCRIPTIVE)
def test_descriptive_text_is_not_blocked(text: str) -> None:
    assert guardian.find_forbidden(text) == []


def test_matching_ignores_accents_and_case() -> None:
    assert guardian.find_forbidden("DEBERÍAS VENDER YA")
    assert guardian.find_forbidden("Te Recomiendo esperar")


def test_detail_quotes_the_original_fragment() -> None:
    verdict = guardian.check(req("Si baja, véndelo."))
    detail = verdict.reasons[0].detail
    assert "véndelo" in detail


def test_normalize_strips_accents_and_lowercases() -> None:
    assert guardian.normalize("Mantén Ñ Deberías") == "manten n deberias"


def test_exempt_names_are_compiled() -> None:
    assert CONFIG.exempt_names
