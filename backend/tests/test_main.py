from fastapi.testclient import TestClient

from app.main import API_PREFIX, discover_routers


def test_health(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["now"].endswith("Z")


def test_discovers_every_api_module_with_a_router() -> None:
    names = [name for name, _ in discover_routers()]
    assert "health" in names
    assert names == sorted(names)


def test_openapi_is_generated(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert f"{API_PREFIX}/health" in response.json()["paths"]
