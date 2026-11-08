"""Los mocks de análisis sirven los ejemplos de §4.3 por la API (criterio de T0-04)."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import API_PREFIX
from app.schemas import examples
from app.schemas.common import Factor
from app.schemas.radar import RadarItem, RadarKind, RadarRule

LAURA = f"{API_PREFIX}/portfolios/laura"
READ_PATHS = ["events", "exposure", "radar", "status", "projection", "agenda", "move"]


@pytest.mark.parametrize(
    ("path", "example"),
    [
        ("exposure", "ExposureOut"),
        ("radar", "RadarOut"),
        ("status", "StatusOut"),
        ("projection", "ProjectionOut"),
        ("move?period=week", "MoveAttributionOut"),
    ],
)
def test_get_serves_example(client: TestClient, path: str, example: str) -> None:
    response = client.get(f"{LAURA}/{path}")
    assert response.status_code == 200
    assert response.json() == examples.load(example)


def test_agenda_lists_examples(client: TestClient) -> None:
    body = client.get(f"{LAURA}/agenda").json()
    assert body == [examples.load("AgendaItemOut"), examples.load("AgendaItemOut.dca")]


def test_scenario_rejects_unknown_factor(client: TestClient) -> None:
    response = client.post(f"{LAURA}/scenarios", json={"factor_shocks": {"GOLD": "-0.10"}})
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_move_echoes_period_and_rejects_unknown(client: TestClient) -> None:
    assert client.get(f"{LAURA}/move", params={"period": "month"}).json()["period"] == "month"
    assert client.get(f"{LAURA}/move", params={"period": "year"}).status_code == 422


@pytest.mark.parametrize("path", READ_PATHS)
def test_unknown_portfolio_is_404(client: TestClient, path: str) -> None:
    response = client.get(f"{API_PREFIX}/portfolios/nadie/{path}")
    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_unknown_portfolio_scenario_is_404(client: TestClient) -> None:
    body = {"factor_shocks": {Factor.EQ_GLOBAL.value: "-0.10"}}
    assert client.post(f"{API_PREFIX}/portfolios/nadie/scenarios", json=body).status_code == 404


def test_opportunity_requires_user_rule() -> None:
    with pytest.raises(ValidationError):
        RadarItem(
            id="rad_x",
            kind=RadarKind.OPPORTUNITY,
            rule=RadarRule.CHEAPER_CONTRIBUTION,
            title="t",
            detail="d",
            user_rule=None,
            calc_id="calc_x",
        )


@pytest.mark.parametrize(
    "name",
    [
        "EventImpactOut",
        "EventImpactOut.nvda",
        "ScenarioRequest",
        "ScenarioOut",
        "MoveAttributionOut",
        "ExposureOut",
        "RadarOut",
        "StatusOut",
        "StatusOut.tranquilo",
        "StatusOut.revisa_plan",
        "ProjectionOut",
        "AgendaItemOut",
        "AgendaItemOut.dca",
    ],
)
def test_contract_has_example(name: str) -> None:
    assert any(Path(p).stem == name for p in examples.example_files())
