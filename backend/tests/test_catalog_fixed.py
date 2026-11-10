"""Catálogo fijo ampliado (T4-26): cada activo de `data/seed/assets.json` se consulta en Yahoo,
tiene sus cierres en `data/prices` hasta el último día de la demo y se puede buscar y valorar."""

import csv
import importlib.util
import json
import re
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import ModuleType
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core import clock
from app.prices import service as prices_service

ROOT = Path(__file__).resolve().parents[2]
ASSETS = json.loads((ROOT / "data" / "seed" / "assets.json").read_text(encoding="utf-8"))["assets"]
YAHOO = [a for a in ASSETS if str(a["price_source"]).startswith("yahoo:")]
ISIN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
DEMO_LAST_DAY = date(2026, 11, 6)
NEW_ASSETS = {
    "IE00B3XXRP09": "VUSA",
    "IE00BFY0GT14": "SPPW",
    "IE00B3RBWM25": "VWRL",
    "US0231351067": "AMZN",
    "US02079K3059": "GOOGL",
    "US30303M1027": "META",
    "US88160R1014": "TSLA",
    "NL0010273215": "ASML",
}


def _check_catalog() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "check_catalog", ROOT / "scripts" / "check_catalog.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_catalog"] = module  # `dataclass` busca su módulo en `sys.modules`
    spec.loader.exec_module(module)
    return module


def test_ids_and_tickers_are_unique() -> None:
    ids = [a["id"] for a in ASSETS]
    tickers = [a["ticker"] for a in ASSETS if a["ticker"]]
    assert len(ids) == len(set(ids))
    assert len(tickers) == len(set(tickers))


def test_new_assets_are_in_the_catalog() -> None:
    by_id = {a["id"]: a for a in ASSETS}
    assert {i: by_id[i]["ticker"] for i in NEW_ASSETS if i in by_id} == NEW_ASSETS


@pytest.mark.parametrize("asset", YAHOO, ids=[a["id"] for a in YAHOO])
def test_yahoo_assets_have_isin_and_supported_currency(asset: dict[str, Any]) -> None:
    assert ISIN.match(asset["id"]) and asset["isin"] == asset["id"]
    assert asset["currency"] in {"EUR", "USD"}  # el único tipo de cambio en directo es EUR/USD


@pytest.mark.parametrize("asset", YAHOO, ids=[a["id"] for a in YAHOO])
def test_yahoo_assets_have_prices_until_the_demo_day(asset: dict[str, Any]) -> None:
    path = ROOT / "data" / "prices" / f"{asset['id']}.csv"
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    days = [date.fromisoformat(r["date"]) for r in rows]
    assert len(rows) >= 500, "menos de 2 años de cierres"
    # Los fondos publican el VL con una sesión de retraso; el resto cierra el último día.
    lag = timedelta(days=3) if asset["price_kind"] == "nav_daily" else timedelta(0)
    assert DEMO_LAST_DAY - lag <= max(days) <= DEMO_LAST_DAY


@pytest.mark.parametrize(
    ("asset_id", "query"), [("US0231351067", "amazon"), ("IE00BFY0GT14", "SPPW")]
)
def test_new_assets_can_be_found(client: TestClient, asset_id: str, query: str) -> None:
    found = client.get("/api/v1/assets/lookup", params={"q": query}).json()

    assert asset_id in [a["id"] for a in found]


@pytest.mark.parametrize("asset_id", sorted(NEW_ASSETS))
def test_new_assets_are_valued_in_demo_mode(asset_id: str) -> None:
    clock.set_now(datetime(2026, 11, 6, 18, 0, tzinfo=UTC))
    try:
        price = prices_service.latest(asset_id)
    finally:
        clock.reset()

    assert price.price > 0
    assert price.price_at.date() == DEMO_LAST_DAY


# --- `scripts/check_catalog.py` ---


def _payload(currency: str, days: int, last: date) -> dict[str, Any]:
    end = int(datetime(last.year, last.month, last.day, 15, tzinfo=UTC).timestamp())
    stamps = [end - 86400 * i for i in reversed(range(days))]
    return {
        "chart": {
            "result": [
                {
                    "meta": {"currency": currency},
                    "timestamp": stamps,
                    "indicators": {"quote": [{"close": [10.0] * days}]},
                }
            ]
        }
    }


def test_check_catalog_accepts_a_good_symbol() -> None:
    check = _check_catalog()
    asset = {"currency": "EUR"}

    assert (
        check.check_chart(asset, _payload("EUR", 700, date(2026, 11, 6)), date(2026, 11, 10)) == []
    )


def test_check_catalog_flags_currency_history_and_stale_quotes() -> None:
    check = _check_catalog()
    today = date(2026, 11, 10)

    assert check.check_chart({"currency": "EUR"}, _payload("GBp", 700, today), today)
    assert check.check_chart({"currency": "USD"}, _payload("EUR", 700, today), today)
    assert check.check_chart({"currency": "EUR"}, _payload("EUR", 100, today), today)
    assert check.check_chart({"currency": "EUR"}, _payload("EUR", 700, date(2026, 10, 1)), today)
    assert check.check_chart({"currency": "EUR"}, {"chart": {"result": []}}, today)


@pytest.mark.live
def test_the_whole_catalog_is_available_in_yahoo() -> None:
    check = _check_catalog()
    with httpx.Client(timeout=15, headers={"User-Agent": "Mozilla/5.0"}) as http:
        checks = check.run(http, datetime.now(UTC).date())

    failed = {c.asset_id: c.problems for c in checks if c.problems}
    assert not failed, failed
    assert len(checks) == len(YAHOO)
