"""Radar de las carteras del seed (`exposure/service.get_radar`, `GET /portfolios/{id}/radar`).

Dorados calculados a mano con los datos del seed (precios del 5 de noviembre de 2026):

Laura (patrimonio 42.363,67 €, plan 70 % renta variable, umbral 0,10):
- Concentración: SALTA. NVIDIA pesa 6,49 % (directa + fondos) y Apple 6,45 %: pasan del 5 %. Además
  las 10 mayores suman 28,62 % (> 25 %). Un solo aviso.
- Divisa: SALTA. EUR 34,86 % y 1,25 % de divisa desconocida: no EUR conocida = 63,89 %.
  El dólar solo, 52,5 %.
- Desviación: NO salta. 75,99 % − 70 % = 5,99 puntos < 10. Tampoco reequilibrio ni traspaso.
- Aportación más barata: SALTA en el fondo principal. Última aportación el 5-oct a 65,4599; último
  precio 62,8352: −4,01 %. El fondo de bonos no cae más de un 3 %.

Javier (patrimonio 180.000,25 €, plan 15 % renta variable):
- Concentración: no (NVIDIA 0,58 %). Divisa: no (no EUR 9,3 %). Desviación: no (15 % − 15 % = 0).
- Aportación más barata: no. Última aportación el 10-oct a 197,2440; hoy 199,9482: sube un 1,37 %.
- Radar vacío.

Laura con un plan del 55 % (para ver oportunidades):
- Desviación: 75,99 % − 55 % = 20,99 puntos → salta (riesgo).
- Reequilibrio con aportaciones: NO salta, porque su DCA (70 % a renta variable) empuja hacia el
  lado equivocado: 0,55 · 300 − 210 = −45 < 0.
- Traspaso sin tributar: SALTA. Hay plusvalía en un fondo traspasable de renta variable (5.269,58 €)
  y tiene un fondo traspasable de renta fija al que ir. `user_rule` = su plan.
"""

from decimal import Decimal

from fastapi.testclient import TestClient

from app.core import trace
from app.exposure import service
from app.main import API_PREFIX
from app.schemas.radar import RadarOut

D = Decimal
LAURA = f"{API_PREFIX}/portfolios/laura"
JAVIER = f"{API_PREFIX}/portfolios/javier"
TOLERANCE = D("0.003")


def _radar(client: TestClient, base: str) -> dict[str, dict[str, object]]:
    body = client.get(f"{base}/radar").json()
    return {item["rule"]: item for item in body["items"]}


def test_laura_radar_has_concentration_and_currency(client: TestClient) -> None:
    items = _radar(client, LAURA)
    assert {"concentration", "currency"} <= set(items)
    assert items["concentration"]["kind"] == items["currency"]["kind"] == "risk"
    concentration = items["concentration"]
    assert abs(D(str(concentration["weight"])) - D("0.0649")) <= TOLERANCE
    assert "NVIDIA" in str(concentration["title"])
    assert "6,5 %" in str(concentration["title"])
    currency = items["currency"]
    assert abs(D(str(currency["weight"])) - D("0.6389")) <= TOLERANCE
    assert "64 %" in str(currency["title"])
    total = D(client.get(LAURA).json()["total_eur"])
    assert abs(D(str(currency["value_eur"])) - total * D("0.6389")) <= D("150")


def test_laura_does_not_drift_nor_rebalance(client: TestClient) -> None:
    items = _radar(client, LAURA)
    for rule in ("drift", "rebalance_with_dca", "tax_free_transfer"):
        assert rule not in items


def test_javier_radar_is_empty(client: TestClient) -> None:
    body = client.get(f"{JAVIER}/radar").json()
    assert body["items"] == []
    assert body["calc_id"].startswith("calc_")


def test_response_validates_against_the_contract(client: TestClient) -> None:
    for base in (LAURA, JAVIER):
        RadarOut.model_validate(client.get(f"{base}/radar").json())


def test_unknown_portfolio_is_404(client: TestClient) -> None:
    assert client.get(f"{API_PREFIX}/portfolios/nadie/radar").status_code == 404


def test_every_item_is_traced_to_the_exposure(client: TestClient) -> None:
    body = client.get(f"{LAURA}/radar").json()
    root = trace.get(body["calc_id"])
    assert root is not None
    assert root.kind == "radar"
    item_ids = {item["calc_id"] for item in body["items"]}
    assert item_ids <= set(root.parent_calc_ids)
    assert len(root.parent_calc_ids) == len(item_ids) + 1  # los avisos y la exposición
    for item in body["items"]:
        record = trace.get(item["calc_id"])
        assert record is not None
        assert record.kind == "radar"
        assert record.formula
        assert record.parent_calc_ids  # apunta a la exposición y a la valoración de la cartera


def test_laura_with_tighter_plan_shows_drift_and_tax_free_transfer(client: TestClient) -> None:
    response = client.put(
        f"{LAURA}/plan",
        json={"target": {"equity": "0.55", "fixed_income": "0.45", "cash": "0.00"}},
    )
    assert response.status_code == 200
    items = _radar(client, LAURA)
    assert abs(D(str(items["drift"]["weight"])) - D("0.2099")) <= TOLERANCE
    assert "rebalance_with_dca" not in items
    transfer = items["tax_free_transfer"]
    assert transfer["kind"] == "opportunity"
    assert transfer["user_rule"] == {"source": "plan", "ref": "laura"}
    assert abs(D(str(transfer["value_eur"])) - D("5269.58")) <= D("1")


def test_laura_cheaper_contribution_for_the_demo(client: TestClient) -> None:
    """Paso 5 del guion, con los datos reales del seed."""
    body = client.get(f"{LAURA}/radar").json()
    cheaper = next(item for item in body["items"] if item["rule"] == "cheaper_contribution")
    assert cheaper["id"] == "rad_cheaper_contribution_IE00B03HD191"
    assert cheaper["kind"] == "opportunity"
    assert cheaper["user_rule"] == {"source": "dca_plan", "ref": "dca_laura"}
    assert abs(D(str(cheaper["weight"])) - D("-0.0401")) <= D("0.0005")
    assert D(str(cheaper["value_eur"])) == D("210.00")  # 300 € · 70 %


def test_service_returns_the_same_as_the_endpoint(client: TestClient) -> None:
    from_service = service.get_radar("laura")
    from_api = RadarOut.model_validate(client.get(f"{LAURA}/radar").json())
    assert [i.rule for i in from_service.items] == [i.rule for i in from_api.items]
