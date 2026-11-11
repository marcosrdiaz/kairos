"""Una cartera sin plan no rompe el replay (TB-03).

Las carteras creadas o importadas nacen sin plan. Antes, `compute_event_impact` pedía el objetivo
del plan y lanzaba `plan_not_found`, así que el replay se cortaba y no se calculaba el impacto de
ninguna cartera. Sin plan no hay clases por debajo del objetivo: el evento nunca sale como
«oportunidad» (se mide frente al plan del usuario), pero sí como riesgo o neutral.
"""

from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.core import clock
from app.events import service as events_service
from app.main import API_PREFIX
from app.schemas.common import Polarity

NOW = datetime(2026, 11, 8, 18, 0, tzinfo=UTC)
EVENT = "nvda-2025-02"
CSV = "asset;units;avg_cost_eur\nNVDA;40;100\n"


@pytest.fixture(autouse=True)
def _clock() -> Iterator[None]:
    clock.set_now(NOW)
    yield


def _import_without_plan(client: TestClient) -> str:
    body = {"name": "Hijos", "kind": "family", "risk_profile": "conservador", "csv": CSV}
    response = client.post(f"{API_PREFIX}/portfolios/import", json=body)
    assert response.status_code == 201, response.text
    portfolio_id: str = response.json()["portfolio"]["id"]
    plan = client.get(f"{API_PREFIX}/portfolios/{portfolio_id}/plan")
    assert plan.status_code == 404  # de verdad nace sin plan
    return portfolio_id


def test_replay_works_with_a_portfolio_without_plan(client: TestClient) -> None:
    new = _import_without_plan(client)
    result = events_service.replay(EVENT)
    assert set(result.portfolios) >= {"laura", "javier", new}
    for portfolio_id in ("laura", "javier", new):
        response = client.get(f"{API_PREFIX}/portfolios/{portfolio_id}/events")
        assert response.status_code == 200, response.text
        assert EVENT in {item["event_id"] for item in response.json()}


def test_without_plan_the_event_is_never_an_opportunity(client: TestClient) -> None:
    new = _import_without_plan(client)
    events_service.replay(EVENT)
    response = client.get(f"{API_PREFIX}/portfolios/{new}/events")
    impact = next(item for item in response.json() if item["event_id"] == EVENT)
    assert impact["polarity"] != Polarity.OPORTUNIDAD.value
    assert impact["calc_id"]
