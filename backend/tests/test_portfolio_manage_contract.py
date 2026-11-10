"""Contrato de crear, editar, borrar e importar carteras y de `POST /ask` (T4-09)."""

import json

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import API_PREFIX
from app.schemas.common import PortfolioKind, Profile, RiskProfile
from app.schemas.portfolio_manage import (
    LEGACY_PROFILE,
    PortfolioCreateRequest,
    PortfolioUpdateRequest,
)

CSV = "asset,units,avg_cost_eur\nIE00BK5BQT80,25,98.40\n"


def test_create_returns_201_with_kind_and_risk_profile(client: TestClient) -> None:
    body = {"name": "  Negocio ", "kind": "business", "risk_profile": "agresivo"}
    response = client.post(f"{API_PREFIX}/portfolios", json=body)

    assert response.status_code == 201
    data = response.json()
    assert data["id"].startswith("pf_")
    assert data["name"] == "Negocio"
    assert data["kind"] == "business"
    assert data["risk_profile"] == "agresivo"
    assert data["profile"] == "dinamico"


def test_create_defaults_to_personal() -> None:
    request = PortfolioCreateRequest.model_validate({"name": "Mía", "risk_profile": "moderado"})
    assert request.kind is PortfolioKind.PERSONAL


@pytest.mark.parametrize(
    "body",
    [
        {"name": "   ", "risk_profile": "moderado"},
        {"name": "Mía"},
        {"name": "Mía", "risk_profile": "dinamico"},
        {"name": "Mía", "risk_profile": "moderado", "profile": "moderado"},
        {"name": "x" * 61, "risk_profile": "moderado"},
    ],
)
def test_create_rejects_invalid_body(client: TestClient, body: dict[str, str]) -> None:
    response = client.post(f"{API_PREFIX}/portfolios", json=body)
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_update_needs_at_least_one_field() -> None:
    with pytest.raises(ValidationError):
        PortfolioUpdateRequest.model_validate({})


def test_update_echoes_changes(client: TestClient) -> None:
    body = {"name": "Hijos", "risk_profile": "conservador"}
    response = client.patch(f"{API_PREFIX}/portfolios/pf_abc", json=body)

    assert response.status_code == 200
    data = response.json()
    assert (data["id"], data["name"], data["risk_profile"]) == ("pf_abc", "Hijos", "conservador")
    assert data["profile"] == "conservador"


def test_delete_returns_204(client: TestClient) -> None:
    response = client.delete(f"{API_PREFIX}/portfolios/pf_abc")
    assert response.status_code == 204
    assert response.content == b""


def test_import_creates_with_201(client: TestClient) -> None:
    body = {"name": "Hijos", "kind": "family", "risk_profile": "conservador", "csv": CSV}
    response = client.post(f"{API_PREFIX}/portfolios/import", json=body)

    assert response.status_code == 201
    data = response.json()
    assert data["dry_run"] is False
    assert data["portfolio"]["name"] == "Hijos"
    assert data["positions"]


def test_import_dry_run_returns_200_without_portfolio(client: TestClient) -> None:
    body = {"name": "Hijos", "risk_profile": "conservador", "csv": CSV, "dry_run": True}
    response = client.post(f"{API_PREFIX}/portfolios/import", json=body)

    assert response.status_code == 200
    assert response.json()["dry_run"] is True
    assert response.json()["portfolio"] is None


def test_import_rejects_empty_csv(client: TestClient) -> None:
    body = {"name": "Hijos", "risk_profile": "conservador", "csv": ""}
    assert client.post(f"{API_PREFIX}/portfolios/import", json=body).status_code == 422


def test_ask_without_portfolio_streams_events(client: TestClient) -> None:
    body = {"question": "¿Cómo van mis carteras?", "channel": "text", "session_id": "s1"}
    response = client.post(f"{API_PREFIX}/ask", json=body)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]
    assert events[0]["type"] == "meta"
    assert events[-1]["type"] == "done"
    assert all("portfolio_ids" in e for e in events if e["type"] == "sentence")


def test_every_risk_profile_has_a_legacy_profile() -> None:
    assert set(LEGACY_PROFILE) == set(RiskProfile)
    assert set(LEGACY_PROFILE.values()) == set(Profile)
