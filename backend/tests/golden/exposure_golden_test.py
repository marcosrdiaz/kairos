"""Dorado del look-through (T1-10, RF-08/RF-09) de Laura y Javier.

Valores esperados en `exposure_cases.json`, calculados aparte (hoja `exposure_sheet.csv`) con
las composiciones de `data/seed/compositions` y los precios fijos de `portfolio_init_cases.json`.
Si el motor cambia y esto no cuadra, se revisa el dorado con el equipo: no se "ajusta".
"""

import json
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from app.core import clock
from app.exposure import service
from app.portfolio import service as portfolio_service
from tests.fakes.price_provider import FakePriceProvider, use_price_provider

GOLDEN = Path(__file__).parent
CASES: dict[str, Any] = json.loads((GOLDEN / "exposure_cases.json").read_text(encoding="utf-8"))
PRICES: dict[str, Any] = json.loads(
    (GOLDEN / "portfolio_init_cases.json").read_text(encoding="utf-8")
)
PORTFOLIOS = ["laura", "javier"]


@pytest.fixture(autouse=True)
def _seeded(db: None) -> Iterator[None]:
    clock.set_now(datetime.fromisoformat(CASES["now"]))
    with use_price_provider(FakePriceProvider(closes=PRICES["closes"], fx=PRICES["fx"])):
        portfolio_service.load_seed(force=True)
        service.load_compositions()
        yield


def _exposure(portfolio_id: str) -> dict[str, Any]:
    out: dict[str, Any] = service.get_exposure(portfolio_id).model_dump(mode="json")
    return out


def _without(items: list[dict[str, Any]], *fields: str) -> list[dict[str, Any]]:
    """Las etiquetas y los nombres son presentación: el dorado compara claves y cifras."""
    return [{k: v for k, v in item.items() if k not in fields} for item in items]


@pytest.mark.parametrize("portfolio_id", PORTFOLIOS)
@pytest.mark.parametrize("dimension", ["by_country", "by_sector", "by_currency"])
def test_buckets_match_golden(portfolio_id: str, dimension: str) -> None:
    out = _exposure(portfolio_id)
    assert _without(out[dimension], "label") == CASES["expected"][portfolio_id][dimension]


@pytest.mark.parametrize("portfolio_id", PORTFOLIOS)
def test_top_companies_match_golden(portfolio_id: str) -> None:
    out = _exposure(portfolio_id)
    assert (
        _without(out["top_companies"], "name") == CASES["expected"][portfolio_id]["top_companies"]
    )


@pytest.mark.parametrize("portfolio_id", PORTFOLIOS)
def test_overlap_matches_golden(portfolio_id: str) -> None:
    out = _exposure(portfolio_id)
    assert _without(out["overlap"], "name") == CASES["expected"][portfolio_id]["overlap"]


@pytest.mark.parametrize("portfolio_id", PORTFOLIOS)
def test_radiography_coverage_and_as_of_match_golden(portfolio_id: str) -> None:
    out = _exposure(portfolio_id)
    expected = CASES["expected"][portfolio_id]
    radiography = out["radiography"]
    radiography["top_country"].pop("label")
    assert radiography == expected["radiography"]
    assert out["coverage_pct"] == expected["coverage_pct"]
    assert out["as_of"] == expected["as_of"]
