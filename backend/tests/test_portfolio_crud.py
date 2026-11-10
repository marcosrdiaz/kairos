"""Crear, renombrar y borrar carteras de verdad (T4-10).

Laura y Javier se siguen cargando por defecto (Q10 abierta); `load_seed(portfolios=False)` deja
la BD solo con el catálogo.
"""

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.alerts.models import Alert
from app.core.db import session_scope
from app.impact.models import EventImpact
from app.main import API_PREFIX
from app.portfolio import service
from app.portfolio.models import DcaPlan, DemoAdjustment, Plan, Portfolio, TaxLot, Transaction

URL = f"{API_PREFIX}/portfolios"
VWCE = "IE00BK5BQT80"


def _create(client: TestClient, **body: Any) -> dict[str, Any]:
    payload = {"name": "Negocio", "kind": "business", "risk_profile": "agresivo", **body}
    response = client.post(URL, json=payload)
    assert response.status_code == 201, response.text
    data: dict[str, Any] = response.json()
    return data


def _count(model: Any, portfolio_id: str) -> int:
    with session_scope() as session:
        stmt = select(func.count()).select_from(model).where(model.portfolio_id == portfolio_id)
        return int(session.scalar(stmt) or 0)


# --- Seed ---


def test_catalog_only_seed_leaves_no_portfolios(db: None) -> None:
    from app.main import create_app

    assert service.load_seed(portfolios=False) == []
    with TestClient(create_app()) as client:
        assert client.get(URL).json() == []
        assert client.get(f"{API_PREFIX}/assets/lookup", params={"q": VWCE}).json()


def test_seed_portfolios_carry_kind_and_risk_profile(client: TestClient) -> None:
    by_id = {p["id"]: p for p in client.get(URL).json()}
    assert by_id["laura"]["kind"] == "personal"
    assert by_id["laura"]["risk_profile"] == "agresivo"
    assert by_id["laura"]["profile"] == "dinamico"
    assert by_id["javier"]["risk_profile"] == "conservador"


# --- Crear ---


def test_create_persists_and_lists_after_the_seed(client: TestClient) -> None:
    created = _create(client, name="  Negocio  ")

    assert created["id"].startswith("pf_")
    assert created["name"] == "Negocio"
    assert (created["kind"], created["risk_profile"], created["profile"]) == (
        "business",
        "agresivo",
        "dinamico",
    )
    ids = [p["id"] for p in client.get(URL).json()]
    assert ids == ["laura", "javier", created["id"]]


def test_created_portfolio_is_empty_and_valued(client: TestClient) -> None:
    created = _create(client)

    data = client.get(f"{URL}/{created['id']}").json()
    assert data["positions"] == []
    assert data["total_eur"] in ("0", "0.00")
    assert data["kind"] == "business"
    assert data["risk_profile"] == "agresivo"


def test_two_creations_get_different_ids(client: TestClient) -> None:
    assert _create(client)["id"] != _create(client)["id"]


def test_created_portfolio_accepts_positions(client: TestClient) -> None:
    created = _create(client)
    body = {"positions": [{"asset_id": VWCE, "units": "10", "avg_cost_eur": "100"}]}

    response = client.post(f"{URL}/{created['id']}/positions", json=body)

    assert response.status_code == 201, response.text
    assert [p["asset_id"] for p in response.json()["positions"]] == [VWCE]


# --- Renombrar ---


def test_update_changes_only_what_is_sent(client: TestClient) -> None:
    created = _create(client)

    response = client.patch(f"{URL}/{created['id']}", json={"name": "Hijos"})

    assert response.status_code == 200
    data = response.json()
    assert (data["name"], data["kind"], data["risk_profile"]) == ("Hijos", "business", "agresivo")
    listed = {p["id"]: p for p in client.get(URL).json()}
    assert listed[created["id"]]["name"] == "Hijos"


def test_update_risk_profile_updates_legacy_profile(client: TestClient) -> None:
    created = _create(client)

    data = client.patch(
        f"{URL}/{created['id']}", json={"kind": "family", "risk_profile": "conservador"}
    ).json()

    assert (data["kind"], data["risk_profile"], data["profile"]) == (
        "family",
        "conservador",
        "conservador",
    )
    assert client.get(f"{URL}/{created['id']}").json()["profile"] == "conservador"


def test_update_unknown_portfolio_is_404(client: TestClient) -> None:
    response = client.patch(f"{URL}/pf_missing", json={"name": "Hijos"})
    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


# --- Borrar ---


def test_delete_removes_the_portfolio(client: TestClient) -> None:
    created = _create(client)

    assert client.delete(f"{URL}/{created['id']}").status_code == 204

    assert client.get(f"{URL}/{created['id']}").status_code == 404
    assert created["id"] not in [p["id"] for p in client.get(URL).json()]


def test_delete_unknown_portfolio_is_404(client: TestClient) -> None:
    response = client.delete(f"{URL}/pf_missing")
    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_delete_removes_everything_of_that_portfolio_only(client: TestClient) -> None:
    replay = client.post(f"{API_PREFIX}/demo/replay/bce-2025-06")
    assert replay.status_code == 200
    javier_before = client.get(f"{URL}/javier").json()["total_eur"]
    assert _count(EventImpact, "laura") > 0
    assert _count(DemoAdjustment, "laura") > 0

    assert client.delete(f"{URL}/laura").status_code == 204

    for model in (Transaction, TaxLot, Plan, DcaPlan, DemoAdjustment, EventImpact, Alert):
        assert _count(model, "laura") == 0, model.__name__
    with session_scope() as session:
        assert session.get(Portfolio, "laura") is None
    assert _count(EventImpact, "javier") > 0
    assert _count(Transaction, "javier") > 0
    assert client.get(f"{URL}/javier").json()["total_eur"] == javier_before
