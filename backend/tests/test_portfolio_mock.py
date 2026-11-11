"""Rutas de cartera que aún sirven el mock (T0-02). La valoración real tiene sus casos dorados en
`tests/golden/portfolio_init*` (T1-03)."""

from fastapi.testclient import TestClient

from app.main import API_PREFIX


def test_get_portfolio_without_prices_is_503(client: TestClient) -> None:
    """Sin CSV en el proveedor (T1-09), la valoración no inventa precios."""
    from tests.fakes.price_provider import FakePriceProvider, use_price_provider

    with use_price_provider(FakePriceProvider()):
        response = client.get(f"{API_PREFIX}/portfolios/laura")
    assert response.status_code == 503
    assert response.json()["code"] == "PRICE_UNAVAILABLE"


def test_list_portfolios(client: TestClient) -> None:
    body = client.get(f"{API_PREFIX}/portfolios").json()
    assert [p["id"] for p in body] == ["laura", "javier", "victor"]


def test_unknown_portfolio_is_404_with_error_shape(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/portfolios/nadie")
    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_transaction_requires_exactly_one_of_amount_or_units(client: TestClient) -> None:
    body = {"type": "buy", "asset_id": "IE00B4L5Y983", "amount_eur": "300.00", "units": "1"}
    response = client.post(f"{API_PREFIX}/portfolios/laura/transactions", json=body)
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_openapi_exposes_portfolio_contracts(client: TestClient) -> None:
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    for name in ("PortfolioOut", "TransactionRequest", "TransferRequest", "DcaPlanCreateRequest"):
        assert name in schemas
