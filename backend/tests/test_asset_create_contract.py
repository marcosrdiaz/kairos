"""Contrato de `POST /assets` (T4-07): alta de un activo que no está en el catálogo."""

from fastapi.testclient import TestClient

from app.schemas.portfolio import AssetOut


def test_create_asset_answers_an_asset(client: TestClient) -> None:
    response = client.post("/api/v1/assets", json={"query": "IE00BK5BQT80"})

    assert response.status_code == 201
    AssetOut.model_validate(response.json())


def test_create_asset_rejects_an_empty_query(client: TestClient) -> None:
    response = client.post("/api/v1/assets", json={"query": ""})

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_create_asset_is_in_the_openapi(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()
    operation = spec["paths"]["/api/v1/assets"]["post"]

    assert "201" in operation["responses"]
    assert {"404", "422", "503"} <= set(operation["responses"])
