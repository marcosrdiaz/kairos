"""Contrato de `GET /portfolios/{id}/history` (T2-18)."""

from fastapi.testclient import TestClient


def test_route_answers_with_the_contract(client: TestClient) -> None:
    response = client.get("/api/v1/portfolios/laura/history", params={"period": "1w"})

    assert response.status_code == 200
    body = response.json()
    assert body["portfolio_id"] == "laura"
    assert body["period"] == "1w"
    assert body["points"] and body["calc_id"].startswith("calc_")


def test_period_defaults_to_one_year(client: TestClient) -> None:
    response = client.get("/api/v1/portfolios/laura/history")

    assert response.json()["period"] == "1y"


def test_unknown_period_is_rejected(client: TestClient) -> None:
    response = client.get("/api/v1/portfolios/laura/history", params={"period": "2w"})

    assert response.status_code == 422
