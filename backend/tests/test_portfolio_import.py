"""Importar una cartera desde CSV (T4-11).

Formato en `PortfolioImportRequest`. Si alguna fila falla no se crea nada y se devuelven todas
las filas que fallan, con su línea, su columna y el motivo.
"""

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import API_PREFIX
from app.portfolio import importer
from app.schemas.portfolio_manage import ImportRowErrorCode

URL = f"{API_PREFIX}/portfolios"
IMPORT = f"{URL}/import"
TEMPLATE = Path(__file__).resolve().parents[2] / "data" / "templates" / "cartera.csv"
TODAY = date(2026, 11, 10)
CATALOG = {
    "IE00BK5BQT80": "IE00BK5BQT80",
    "VWCE": "IE00BK5BQT80",
    "AAPL": "US0378331005",
    "NVDA": "US67066G1040",
    "MSFT": "US5949181045",
    "ITX": "ES0148396007",
    "IBE": "ES0144580Y14",
}


def _resolve(code: str) -> str | None:
    return CATALOG.get(code.upper())


def _parse(csv: str) -> importer.ParsedCsv:
    return importer.parse(csv, _resolve, TODAY)


def _codes(parsed: importer.ParsedCsv) -> list[tuple[int, str | None, ImportRowErrorCode]]:
    return [(e.line, e.field, e.code) for e in parsed.errors]


def _body(csv: str, **extra: Any) -> dict[str, Any]:
    return {"name": "Hijos", "kind": "family", "risk_profile": "conservador", "csv": csv, **extra}


# --- Lectura del CSV (función pura) ---


def test_parse_reads_isin_and_ticker_with_optional_date() -> None:
    parsed = _parse("asset,units,avg_cost_eur,acquired_at\nIE00BK5BQT80,25,98.40,2024-09-02\n")

    assert parsed.errors == []
    [line] = parsed.positions
    assert line.asset_id == "IE00BK5BQT80"
    assert line.units == Decimal("25")
    assert line.avg_cost_eur == Decimal("98.40")
    assert line.acquired_at == datetime(2024, 9, 2, tzinfo=UTC)


def test_parse_accepts_semicolons_decimal_commas_bom_and_any_case() -> None:
    csv = "﻿Asset ; Units ; AVG_COST_EUR\n vwce ; 40,5 ; 91,10\n\naapl;3;150\n"

    parsed = _parse(csv)

    assert parsed.errors == []
    assert [(p.asset_id, p.units, p.avg_cost_eur, p.acquired_at) for p in parsed.positions] == [
        ("IE00BK5BQT80", Decimal("40.5"), Decimal("91.10"), None),
        ("US0378331005", Decimal("3"), Decimal("150"), None),
    ]


def test_parse_ignores_extra_columns() -> None:
    parsed = _parse("asset,notes,units,avg_cost_eur\nVWCE,para la universidad,1,100\n")
    assert parsed.errors == []
    assert len(parsed.positions) == 1


def test_parse_without_rows_is_empty_file() -> None:
    assert _codes(_parse("asset,units,avg_cost_eur\n")) == [
        (1, None, ImportRowErrorCode.EMPTY_FILE)
    ]
    assert _codes(_parse("\n \n")) == [(1, None, ImportRowErrorCode.EMPTY_FILE)]


def test_parse_reports_each_missing_column() -> None:
    assert _codes(_parse("asset,units\nVWCE,1\n")) == [
        (1, "avg_cost_eur", ImportRowErrorCode.MISSING_COLUMN)
    ]


def test_parse_reports_every_bad_row_with_its_line() -> None:
    csv = (
        "asset,units,avg_cost_eur,acquired_at\n"
        "VWCE,10,100,\n"  # línea 2: bien
        "XX0000000000,1,1,\n"  # 3: no está en el catálogo
        "NVDA,0,150,\n"  # 4: participaciones a cero
        "MSFT,1,-3,\n"  # 5: coste negativo
        "ITX,1,abc,2024-13-01\n"  # 6: coste y fecha no válidos
        "IE00BK5BQT80,2,90,\n"  # 7: VWCE repetido (por ISIN)
        "IBE,1,1,2099-01-01\n"  # 8: fecha futura
        "AAPL,1.000,50\n"  # 9: bien (punto decimal); falta la fecha opcional
        ",1,1,\n"  # 10: sin activo
        "msft,2,10,\n"  # 11: repetido aunque la línea 5 tuviera otro error
    )

    parsed = _parse(csv)

    assert _codes(parsed) == [
        (3, "asset", ImportRowErrorCode.UNKNOWN_ASSET),
        (4, "units", ImportRowErrorCode.INVALID_VALUE),
        (5, "avg_cost_eur", ImportRowErrorCode.INVALID_VALUE),
        (6, "avg_cost_eur", ImportRowErrorCode.INVALID_VALUE),
        (6, "acquired_at", ImportRowErrorCode.INVALID_VALUE),
        (7, "asset", ImportRowErrorCode.DUPLICATE_ASSET),
        (8, "acquired_at", ImportRowErrorCode.INVALID_VALUE),
        (10, "asset", ImportRowErrorCode.INVALID_VALUE),
        (11, "asset", ImportRowErrorCode.DUPLICATE_ASSET),
    ]
    assert all(e.message for e in parsed.errors)


@pytest.mark.parametrize("value", ["1.234,5", "1e3", "NaN", "Infinity", "0.123456789"])
def test_parse_rejects_ambiguous_or_too_precise_numbers(value: str) -> None:
    parsed = _parse(f'asset,units,avg_cost_eur\nVWCE,"{value}",1\n')
    assert _codes(parsed) == [(2, "units", ImportRowErrorCode.INVALID_VALUE)]


# --- API ---


def test_import_creates_the_portfolio_with_its_positions(client: TestClient) -> None:
    csv = "asset;units;avg_cost_eur;acquired_at\nVWCE;25;98,40;2024-09-02\nAAPL;3;150;\n"

    response = client.post(IMPORT, json=_body(csv))

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["dry_run"] is False
    portfolio = data["portfolio"]
    assert (portfolio["name"], portfolio["kind"], portfolio["risk_profile"]) == (
        "Hijos",
        "family",
        "conservador",
    )
    assert [p["asset_id"] for p in data["positions"]] == ["IE00BK5BQT80", "US0378331005"]
    assert data["positions"][0]["acquired_at"] == "2024-09-02T00:00:00Z"

    valued = client.get(f"{URL}/{portfolio['id']}").json()
    units = {p["asset_id"]: Decimal(p["units"]) for p in valued["positions"]}
    assert units == {"IE00BK5BQT80": Decimal("25"), "US0378331005": Decimal("3")}
    assert portfolio["id"] in [p["id"] for p in client.get(URL).json()]


def test_dry_run_validates_without_creating(client: TestClient) -> None:
    before = client.get(URL).json()

    response = client.post(IMPORT, json=_body("asset,units,avg_cost_eur\nVWCE,1,1\n", dry_run=True))

    assert response.status_code == 200
    data = response.json()
    assert (data["dry_run"], data["portfolio"]) == (True, None)
    assert [p["asset_id"] for p in data["positions"]] == ["IE00BK5BQT80"]
    assert client.get(URL).json() == before


@pytest.mark.parametrize("dry_run", [False, True])
def test_bad_rows_create_nothing_and_list_the_failures(client: TestClient, dry_run: bool) -> None:
    before = client.get(URL).json()
    csv = "asset,units,avg_cost_eur\nVWCE,1,1\nXX0000000000,1,1\n"

    response = client.post(IMPORT, json=_body(csv, dry_run=dry_run))

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    [row] = body["details"]["rows"]
    assert (row["line"], row["field"], row["code"]) == (3, "asset", "unknown_asset")
    assert "XX0000000000" in row["message"]
    assert client.get(URL).json() == before


def test_template_imports_cleanly(client: TestClient) -> None:
    csv = TEMPLATE.read_text(encoding="utf-8")

    response = client.post(IMPORT, json=_body(csv, dry_run=True))

    assert response.status_code == 200, response.text
    assert response.json()["positions"]
