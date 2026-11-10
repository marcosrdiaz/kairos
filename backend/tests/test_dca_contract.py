"""Contrato de las ejecuciones DCA: `GET /portfolios/{id}/dca-executions` y `POST /demo/dca/run`.

Solo forma y códigos de error; el comportamiento real (T1-06) está en `test_dca.py`.
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from app.main import API_PREFIX
from app.schemas.portfolio import DcaExecutionOut

EXECUTIONS = TypeAdapter(list[DcaExecutionOut])


def test_demo_dca_run_returns_executions(client: TestClient) -> None:
    response = client.post(f"{API_PREFIX}/demo/dca/run")
    assert response.status_code == 200
    executions = EXECUTIONS.validate_python(response.json())
    assert all(e.status == "pending" for e in executions)


def test_demo_dca_run_disabled_outside_demo_mode(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.config import get_settings

    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "yahoo")  # producción exige precios en directo
    get_settings.cache_clear()
    response = client.post(f"{API_PREFIX}/demo/dca/run")
    assert response.status_code == 403
    assert response.json()["code"] == "DEMO_MODE_DISABLED"


@pytest.mark.parametrize("status", ["pending", "confirmed", "skipped"])
def test_list_executions_filters_by_status(client: TestClient, status: str) -> None:
    client.post(f"{API_PREFIX}/demo/dca/run")
    response = client.get(
        f"{API_PREFIX}/portfolios/laura/dca-executions", params={"status": status}
    )
    assert response.status_code == 200
    assert all(e.status == status for e in EXECUTIONS.validate_python(response.json()))


def test_list_executions_without_filter(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/portfolios/laura/dca-executions")
    assert response.status_code == 200
    EXECUTIONS.validate_python(response.json())


def test_list_executions_unknown_portfolio(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/portfolios/nadie/dca-executions")
    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_list_executions_rejects_unknown_status(client: TestClient) -> None:
    response = client.get(
        f"{API_PREFIX}/portfolios/laura/dca-executions", params={"status": "otro"}
    )
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_openapi_exposes_dca_execution_routes(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert "get" in paths[f"{API_PREFIX}/portfolios/{{portfolio_id}}/dca-executions"]
    assert "post" in paths[f"{API_PREFIX}/demo/dca/run"]
