"""Composición de fondos y ETF de T1-08 (`data/seed/compositions/<ISIN>.csv`).

Comprueba el formato (columnas, pesos que suman 1, claves en mayúsculas, `as_of` y `source`)
y que cada fondo o ETF de `data/seed/assets.json` tiene su CSV.
"""

import csv
import json
import re
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

SEED = Path(__file__).resolve().parents[2] / "data" / "seed"
COMP_DIR = SEED / "compositions"
COLUMNS = ["constituent_key", "name", "weight", "country", "sector", "currency", "as_of", "source"]
SECTORS = {
    "information_technology",
    "financials",
    "industrials",
    "health_care",
    "consumer_discretionary",
    "communication_services",
    "consumer_staples",
    "energy",
    "materials",
    "utilities",
    "real_estate",
    "government",
    "corporate",
    "other",
}
KEY = re.compile(r"^[A-Z0-9_]+$")
NON_COMPANY_PREFIXES = ("OTROS_", "GOV_", "BONOS_")
HEDGED_FUNDS = {"IE00B18GC888"}  # Vanguard Global Bond EUR Hedged: la divisa es EUR (D-XXX)


def _assets() -> list[dict[str, str]]:
    data = json.loads((SEED / "assets.json").read_text(encoding="utf-8"))
    return list(data["assets"])


def _funds() -> list[str]:
    return [a["id"] for a in _assets() if a["asset_type"] in ("fund", "etf")]


def _rows(isin: str) -> list[dict[str, str]]:
    with open(COMP_DIR / f"{isin}.csv", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_every_fund_and_etf_has_a_composition_file() -> None:
    missing = [isin for isin in _funds() if not (COMP_DIR / f"{isin}.csv").exists()]
    assert not missing, f"faltan CSV de composición: {missing}"


def test_no_composition_file_without_asset() -> None:
    known = set(_funds())
    extra = [p.stem for p in COMP_DIR.glob("*.csv") if p.stem not in known]
    assert not extra, f"CSV sin fondo/ETF en assets.json: {extra}"


@pytest.mark.parametrize("isin", _funds())
def test_columns_and_weights(isin: str) -> None:
    with open(COMP_DIR / f"{isin}.csv", encoding="utf-8", newline="") as fh:
        assert next(csv.reader(fh)) == COLUMNS
    rows = _rows(isin)
    assert rows, "CSV vacío"
    weights = [Decimal(r["weight"]) for r in rows]
    assert all(w > 0 for w in weights)
    assert abs(sum(weights, Decimal(0)) - 1) <= Decimal("0.0001")


@pytest.mark.parametrize("isin", _funds())
def test_keys_are_uppercase_and_unique(isin: str) -> None:
    keys = [r["constituent_key"] for r in _rows(isin)]
    assert len(keys) == len(set(keys)), "claves repetidas"
    bad = [k for k in keys if not KEY.match(k) or len(k) > 64]
    assert not bad, f"claves no válidas (mayúsculas, dígitos y _): {bad}"


@pytest.mark.parametrize("isin", _funds())
def test_as_of_source_and_dimensions(isin: str) -> None:
    for r in _rows(isin):
        date.fromisoformat(r["as_of"])
        assert r["name"].strip(), r
        assert r["source"].strip() and len(r["source"]) <= 300, r["constituent_key"]
        assert re.fullmatch(r"[A-Z]{2}|OTHER", r["country"]), r
        assert r["sector"] in SECTORS, r
        assert re.fullmatch(r"[A-Z]{3}|", r["currency"]), r


@pytest.mark.parametrize("isin", _funds())
def test_residual_rows_carry_their_country(isin: str) -> None:
    """`OTROS_<país>...` lleva ese país; así la exposición por país sale completa."""
    for r in _rows(isin):
        key = r["constituent_key"]
        if key.startswith("OTROS_"):
            cc = key.removeprefix("OTROS_").split("_")[0]
            assert r["country"] == cc, key


@pytest.mark.parametrize("isin", sorted(HEDGED_FUNDS))
def test_hedged_funds_have_base_currency(isin: str) -> None:
    assert {r["currency"] for r in _rows(isin)} == {"EUR"}


def test_direct_stocks_share_keys_with_fund_companies() -> None:
    """Las acciones directas de `assets.json` (clave = ticker) están en IWDA con esa clave."""
    iwda = {r["constituent_key"] for r in _rows("IE00B4L5Y983")}
    tickers = {a["ticker"] for a in _assets() if a["asset_type"] == "stock"}
    assert tickers <= iwda, tickers - iwda


def test_company_keys_do_not_clash_across_countries() -> None:
    """Un mismo nombre de clave de empresa no puede ser dos empresas (p. ej. SAN, SAP)."""
    seen: dict[str, str] = {}
    for isin in ("IE00B4L5Y983", "IE00B5BMR087"):
        for r in _rows(isin):
            key = r["constituent_key"]
            if key.startswith(NON_COMPANY_PREFIXES):
                continue
            assert seen.setdefault(key, r["country"]) == r["country"], key
