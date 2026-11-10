"""`GET /portfolios/{id}/ticker` (T2-17) sobre el seed y los CSV reales de `data/prices`."""

from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core import clock
from app.portfolio import service as portfolio_service
from app.prices import service as prices_service

NOW = datetime(2026, 11, 8, 18, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _fixed_clock() -> Iterator[None]:
    clock.set_now(NOW)
    yield


def test_one_item_per_position_in_portfolio_order(client: TestClient) -> None:
    response = client.get("/api/v1/portfolios/laura/ticker")

    assert response.status_code == 200
    body = response.json()
    assert body["portfolio_id"] == "laura"
    assert body["as_of"] == "2026-11-08T18:00:00Z"
    positions = portfolio_service.get_valued("laura").positions
    assert [i["asset_id"] for i in body["items"]] == [p.asset_id for p in positions]


def test_prices_and_changes_come_from_prices_history(client: TestClient) -> None:
    items = client.get("/api/v1/portfolios/laura/ticker").json()["items"]

    with_change = [i for i in items if i["change_pct"] is not None]
    assert with_change, "Laura tiene activos con histórico: alguno debe tener variación"
    for item in with_change:
        latest = prices_service.latest(item["asset_id"])
        assert Decimal(item["price"]) == latest.price
        previous = Decimal(item["previous_price"])
        expected = (latest.price - previous) / previous
        assert abs(Decimal(item["change_pct"]) - expected) < Decimal("0.000001")
        assert item["previous_price_at"] < item["price_at"] <= "2026-11-08T18:00:00Z"


def test_every_item_is_traceable(client: TestClient) -> None:
    items = client.get("/api/v1/portfolios/javier/ticker").json()["items"]

    assert items
    for item in items:
        trace = client.get(f"/api/v1/traces/{item['calc_id']}")
        assert trace.status_code == 200
        assert trace.json()["outputs"]["change_pct"] == item["change_pct"]


def test_unknown_portfolio_is_404(client: TestClient) -> None:
    response = client.get("/api/v1/portfolios/nadie/ticker")

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"
