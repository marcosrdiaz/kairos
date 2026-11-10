"""Contrato de `GET /portfolios/{id}/positions/{asset_id}/history` (T2-23)."""

from fastapi.testclient import TestClient

from app.schemas.impact import AssetImpact

NVDA = "US67066G1040"
URL = f"/api/v1/portfolios/laura/positions/{NVDA}/history"


def test_route_answers_with_the_contract(client: TestClient) -> None:
    response = client.get(URL, params={"period": "1m"})

    assert response.status_code == 200
    body = response.json()
    assert body["portfolio_id"] == "laura"
    assert body["asset_id"] == NVDA
    assert body["period"] == "1m"
    assert body["calc_id"].startswith("calc_")
    point = body["points"][0]
    assert {"date", "value_eur", "flows_eur", "price", "units"} <= point.keys()


def test_period_defaults_to_one_year(client: TestClient) -> None:
    assert client.get(URL).json()["period"] == "1y"


def test_unknown_period_is_rejected(client: TestClient) -> None:
    assert client.get(URL, params={"period": "2w"}).status_code == 422


def test_asset_impact_range_is_optional() -> None:
    """Los impactos guardados antes de T2-23 no traen el rango por posición."""
    old = AssetImpact.model_validate(
        {
            "asset_id": NVDA,
            "name": "NVIDIA Corp.",
            "value_eur": "1258.67",
            "impact_eur": "-180.00",
            "market_eur": "-180.00",
            "fx_eur": "0.00",
            "channel": "resultados NVDA",
        }
    )

    assert old.low_eur is None and old.high_eur is None
