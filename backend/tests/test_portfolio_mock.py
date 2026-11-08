"""El mock de cartera sirve los ejemplos por la API (criterio de T0-02)."""

from fastapi.testclient import TestClient

from app.main import API_PREFIX
from app.schemas import examples


def test_get_laura_serves_example(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/portfolios/laura")
    assert response.status_code == 200
    assert response.json() == examples.load("PortfolioOut")


def test_get_javier(client: TestClient) -> None:
    body = client.get(f"{API_PREFIX}/portfolios/javier").json()
    assert body["id"] == "javier"
    assert body["profile"] == "conservador"


def test_list_portfolios(client: TestClient) -> None:
    body = client.get(f"{API_PREFIX}/portfolios").json()
    assert [p["id"] for p in body] == ["laura", "javier"]


def test_unknown_portfolio_is_404_with_error_shape(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/portfolios/nadie")
    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_plan_and_dca_plans(client: TestClient) -> None:
    plan = client.get(f"{API_PREFIX}/portfolios/laura/plan").json()
    assert plan == examples.load("PlanOut")
    dca = client.get(f"{API_PREFIX}/portfolios/laura/dca-plans").json()
    assert dca == [examples.load("DcaPlanOut")]


def test_transaction_returns_example(client: TestClient) -> None:
    response = client.post(
        f"{API_PREFIX}/portfolios/laura/transactions", json=examples.load("TransactionRequest.sell")
    )
    assert response.status_code == 201
    assert response.json() == examples.load("TransactionOut")


def test_transaction_requires_exactly_one_of_amount_or_units(client: TestClient) -> None:
    body = {"type": "buy", "asset_id": "IE00B4L5Y983", "amount_eur": "300.00", "units": "1"}
    response = client.post(f"{API_PREFIX}/portfolios/laura/transactions", json=body)
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_fund_to_fund_transfer(client: TestClient) -> None:
    response = client.post(
        f"{API_PREFIX}/portfolios/laura/transfers", json=examples.load("TransferRequest")
    )
    assert response.status_code == 201
    assert response.json()["type"] == "transfer"


def test_etf_transfer_not_allowed(client: TestClient) -> None:
    body = {"from_asset_id": "IE00B4L5Y983", "to_asset_id": "IE00B03HD191", "units": "50"}
    response = client.post(f"{API_PREFIX}/portfolios/laura/transfers", json=body)
    assert response.status_code == 422
    error = response.json()
    assert error["code"] == "TRANSFER_NOT_ALLOWED"
    assert error["details"]["from_asset_type"] == "etf"
    assert error["details"]["alternative"] == "sell_and_buy"


def test_dca_execution_skip(client: TestClient) -> None:
    response = client.post(f"{API_PREFIX}/dca-executions/dcx_1", json={"action": "skip"})
    assert response.status_code == 200
    assert response.json()["status"] == "skipped"


def test_openapi_exposes_portfolio_contracts(client: TestClient) -> None:
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    for name in ("PortfolioOut", "TransactionRequest", "TransferRequest", "DcaPlanCreateRequest"):
        assert name in schemas
