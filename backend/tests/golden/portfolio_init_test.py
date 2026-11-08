"""Casos dorados del alta (T1-03, RF-01/RF-02/RF-03): Laura y Javier desde `data/seed`.

Los precios y los valores esperados están en `portfolio_init_cases.json`, calculados aparte.
"""

import json
from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from app.core import clock, trace
from app.portfolio import service
from app.schemas.common import PriceKind, SourceKind, TraceKind
from tests.fakes.price_provider import FakePriceProvider, use_price_provider

CASES: dict[str, Any] = json.loads(
    (Path(__file__).parent / "portfolio_init_cases.json").read_text(encoding="utf-8")
)
POSITION_FIELDS = [
    "asset_id",
    "units",
    "avg_cost_eur",
    "price",
    "price_currency",
    "fx_rate",
    "price_at",
    "value_eur",
    "weight",
    "unrealized_pnl_eur",
    "first_acquired_at",
]


@pytest.fixture(autouse=True)
def _seeded(db: None) -> Iterator[None]:
    clock.set_now(datetime.fromisoformat(CASES["now"]))
    with use_price_provider(FakePriceProvider(closes=CASES["closes"], fx=CASES["fx"])):
        service.load_seed(force=True)
        yield


@pytest.mark.parametrize("portfolio_id", ["laura", "javier"])
def test_valuation_matches_golden(portfolio_id: str) -> None:
    expected = CASES["expected"][portfolio_id]
    out = service.get_valued(portfolio_id).model_dump(mode="json")
    assert out["id"] == portfolio_id
    assert out["total_eur"] == expected["total_eur"]
    assert out["change_week_eur"] == expected["change_week_eur"]
    assert out["change_week_pct"] == expected["change_week_pct"]
    assert out["allocation"] == expected["allocation"]
    assert [{k: p[k] for k in POSITION_FIELDS} for p in out["positions"]] == expected["positions"]
    assert out["demo_adjustments"] == []
    assert out["valued_at"] == CASES["now"]


def test_total_is_sum_of_positions() -> None:
    out = service.get_valued("laura")
    assert out.total_eur == sum((p.value_eur for p in out.positions), Decimal(0))


def test_positions_carry_catalog_data() -> None:
    by_id = {p.asset_id: p for p in service.get_valued("laura").positions}
    fund, etf, stock = by_id["IE00B03HD191"], by_id["IE00B4L5Y983"], by_id["US0378331005"]
    assert (fund.asset_type, fund.price_kind) == ("fund", PriceKind.NAV_DAILY)
    assert fund.transferable is True
    assert (etf.ticker, etf.transferable) == ("IWDA", False)
    assert stock.name == "Apple Inc."


def test_profiles_and_names() -> None:
    laura, javier = service.get_valued("laura"), service.get_valued("javier")
    assert (laura.name, laura.profile) == ("Laura", "dinamico")
    assert (javier.name, javier.profile) == ("Javier", "conservador")


def test_valuation_is_traced() -> None:
    out = service.get_valued("laura")
    record = trace.get(out.calc_id)
    assert record is not None
    assert record.kind == TraceKind.VALUATION
    assert record.outputs["total_eur"] == CASES["expected"]["laura"]["total_eur"]
    kinds = {(s["kind"], s["ref"]) for s in record.sources}
    assert (SourceKind.PRICE, "US0378331005") in kinds
    assert (SourceKind.FX, "EURUSD") in kinds
