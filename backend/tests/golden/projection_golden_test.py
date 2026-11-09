"""Dorado de la proyección con DCA (T1-10, RF-22, paso 7 "¿Voy bien?") de Laura y Javier.

Valores esperados en `projection_cases.json`, calculados aparte (hoja `projection_sheet.csv`) con
las reglas de D-064, el plan y el DCA del seed y los precios fijos de `portfolio_init_cases.json`.
Si el motor cambia y esto no cuadra, se revisa el dorado con el equipo: no se "ajusta".
"""

import json
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from app.core import clock
from app.planning import service
from app.portfolio import service as portfolio_service
from tests.fakes.price_provider import FakePriceProvider, use_price_provider

GOLDEN = Path(__file__).parent
CASES: dict[str, Any] = json.loads((GOLDEN / "projection_cases.json").read_text(encoding="utf-8"))
PRICES: dict[str, Any] = json.loads(
    (GOLDEN / "portfolio_init_cases.json").read_text(encoding="utf-8")
)
FIELDS = [
    "goal_amount_eur",
    "goal_year",
    "current_value_eur",
    "monthly_contribution_eur",
    "scenarios",
    "on_track",
    "gap_eur",
]


@pytest.fixture(autouse=True)
def _seeded(db: None) -> Iterator[None]:
    clock.set_now(datetime.fromisoformat(CASES["now"]))
    with use_price_provider(FakePriceProvider(closes=PRICES["closes"], fx=PRICES["fx"])):
        portfolio_service.load_seed(force=True)
        yield


@pytest.mark.parametrize("portfolio_id", ["laura", "javier"])
def test_projection_matches_golden(portfolio_id: str) -> None:
    out = service.get_projection(portfolio_id).model_dump(mode="json")
    expected = CASES["expected"][portfolio_id]
    assert {k: out[k] for k in FIELDS} == {k: expected[k] for k in FIELDS}


def test_laura_is_on_track_in_the_base_scenario() -> None:
    """Paso 7 del guion (§5): Laura llega a su meta en el escenario base."""
    assert CASES["expected"]["laura"]["on_track"] is True
    assert service.get_projection("laura").on_track is True
