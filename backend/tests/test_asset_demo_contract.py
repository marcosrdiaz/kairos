"""Contratos de `/assets/lookup`, `/demo/reset` y `PriceOut` sobre el mock (contrato de T1-03)."""

import pytest
from fastapi.testclient import TestClient

from app.main import API_PREFIX
from app.schemas import examples


@pytest.mark.parametrize(
    ("q", "expected"),
    [
        ("IWDA", "AssetOut"),
        ("iwda", "AssetOut"),
        ("IE00B03HD191", "AssetOut.fund"),
        ("apple", "AssetOut.stock"),
    ],
)
def test_lookup_by_isin_ticker_or_name(client: TestClient, q: str, expected: str) -> None:
    response = client.get(f"{API_PREFIX}/assets/lookup", params={"q": q})
    assert response.status_code == 200
    assert response.json() == [examples.load(expected)]


def test_lookup_without_matches_is_empty(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/assets/lookup", params={"q": "zzz"})
    assert response.status_code == 200
    assert response.json() == []


def test_lookup_requires_query(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/assets/lookup", params={"q": ""})
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("body", [None, {"preload": False}, {"preload": True}])
def test_demo_reset_reloads_both_portfolios(
    client: TestClient, body: dict[str, bool] | None
) -> None:
    response = client.post(f"{API_PREFIX}/demo/reset", json=body)
    assert response.status_code == 200
    assert response.json()["portfolio_ids"] == ["laura", "javier", "victor"]


def test_demo_reset_disabled_outside_demo_mode(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.config import get_settings

    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "yahoo")  # producción exige precios en directo
    get_settings.cache_clear()
    response = client.post(f"{API_PREFIX}/demo/reset")
    assert response.status_code == 403
    assert response.json()["code"] == "DEMO_MODE_DISABLED"


def test_openapi_exposes_new_contracts(client: TestClient) -> None:
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    for name in ("AssetOut", "DemoResetRequest", "DemoResetOut"):
        assert name in schemas
