"""Alta de posiciones, seed idempotente, `/demo/reset` y `/assets/lookup` (T1-03)."""

import json
from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core import clock
from app.core.errors import AppError, ErrorCode
from app.main import API_PREFIX
from app.portfolio import service
from app.schemas.portfolio import PositionInitLine, PositionsInitRequest
from tests.fakes.price_provider import FakePriceProvider, use_price_provider

CASES: dict[str, Any] = json.loads(
    (Path(__file__).parent / "portfolio_init_cases.json").read_text(encoding="utf-8")
)
LAURA_TOTAL = Decimal(CASES["expected"]["laura"]["total_eur"])


@pytest.fixture(autouse=True)
def _prices() -> Iterator[None]:
    clock.set_now(datetime.fromisoformat(CASES["now"]))
    with use_price_provider(FakePriceProvider(closes=CASES["closes"], fx=CASES["fx"])):
        yield


def _init(asset_id: str, units: str, cost: str, acquired_at: datetime | None = None) -> Any:
    line = PositionInitLine(
        asset_id=asset_id,
        units=Decimal(units),
        avg_cost_eur=Decimal(cost),
        acquired_at=acquired_at,
    )
    return PositionsInitRequest(positions=[line])


# --- Seed ---


def test_seed_is_idempotent(db: None) -> None:
    assert service.load_seed() == ["laura", "javier", "victor"]
    first = service.get_valued("laura").total_eur
    service.load_seed()
    assert service.get_valued("laura").total_eur == first == LAURA_TOTAL


def test_seed_without_force_keeps_user_changes(db: None) -> None:
    service.load_seed()
    service.init_positions("laura", _init("IE00B4L5Y983", "10", "90"))
    service.load_seed()
    assert service.get_valued("laura").total_eur == LAURA_TOTAL + Decimal("954.20")


def test_list_portfolio_ids(db: None) -> None:
    service.load_seed()
    assert service.list_portfolio_ids() == ["laura", "javier", "victor"]
    assert [p.id for p in service.list_portfolios()] == ["laura", "javier", "victor"]


# --- Alta ---


def test_init_adds_a_lot_and_revalues(db: None) -> None:
    service.load_seed()
    out = service.init_positions("laura", _init("IE00B4L5Y983", "10", "90"))
    iwda = next(p for p in out.positions if p.asset_id == "IE00B4L5Y983")
    assert iwda.units == Decimal("124")
    assert iwda.value_eur == Decimal("11832.08")  # 124 × 95,42
    assert out.total_eur == LAURA_TOTAL + Decimal("954.20")


def test_init_new_asset_defaults_acquired_at_to_now(db: None) -> None:
    service.load_seed()
    out = service.init_positions("laura", _init("DEP-12M", "1000", "1"))
    dep = next(p for p in out.positions if p.asset_id == "DEP-12M")
    assert dep.first_acquired_at == datetime(2026, 11, 8, 18, 0, tzinfo=UTC)
    assert dep.value_eur == Decimal("1000.00")
    assert dep.asset_class == "cash"


def test_init_unknown_asset_is_not_found_and_changes_nothing(db: None) -> None:
    service.load_seed()
    request = PositionsInitRequest(
        positions=[
            PositionInitLine(asset_id="IE00B4L5Y983", units=Decimal(1), avg_cost_eur=Decimal(1)),
            PositionInitLine(asset_id="XX0000000000", units=Decimal(1), avg_cost_eur=Decimal(1)),
        ]
    )
    with pytest.raises(AppError) as exc:
        service.init_positions("laura", request)
    assert exc.value.code is ErrorCode.NOT_FOUND
    assert exc.value.details["asset_id"] == "XX0000000000"
    assert service.get_valued("laura").total_eur == LAURA_TOTAL


def test_init_without_price_changes_nothing(db: None) -> None:
    service.load_seed()
    with pytest.raises(AppError) as exc:
        service.init_positions("laura", _init("IE00B5BMR087", "1", "1"))  # sin precios
    assert exc.value.code is ErrorCode.PRICE_UNAVAILABLE
    assert service.get_valued("laura").total_eur == LAURA_TOTAL


def test_init_unknown_portfolio(db: None) -> None:
    service.load_seed()
    with pytest.raises(AppError) as exc:
        service.init_positions("nadie", _init("IE00B4L5Y983", "1", "1"))
    assert exc.value.code is ErrorCode.NOT_FOUND


def test_ensure_exists(db: None) -> None:
    service.load_seed()
    service.ensure_exists("laura")
    with pytest.raises(AppError) as exc:
        service.ensure_exists("nadie")
    assert exc.value.code is ErrorCode.NOT_FOUND


# --- API ---


def test_api_get_portfolio(client: TestClient) -> None:
    body = client.get(f"{API_PREFIX}/portfolios/laura").json()
    assert body["total_eur"] == CASES["expected"]["laura"]["total_eur"]
    assert body["calc_id"].startswith("calc_")


def test_api_init_positions(client: TestClient) -> None:
    body = {"positions": [{"asset_id": "IE00B4L5Y983", "units": "10", "avg_cost_eur": "90"}]}
    response = client.post(f"{API_PREFIX}/portfolios/laura/positions", json=body)
    assert response.status_code == 201
    assert Decimal(response.json()["total_eur"]) == LAURA_TOTAL + Decimal("954.20")


def test_api_init_unknown_asset_is_404(client: TestClient) -> None:
    body = {"positions": [{"asset_id": "XX0000000000", "units": "1", "avg_cost_eur": "1"}]}
    response = client.post(f"{API_PREFIX}/portfolios/laura/positions", json=body)
    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_api_demo_reset_restores_seed(client: TestClient) -> None:
    body = {"positions": [{"asset_id": "IE00B4L5Y983", "units": "10", "avg_cost_eur": "90"}]}
    client.post(f"{API_PREFIX}/portfolios/laura/positions", json=body)
    response = client.post(f"{API_PREFIX}/demo/reset", json={"preload": False})
    assert response.status_code == 200
    assert response.json() == {
        "portfolio_ids": ["laura", "javier", "victor"],
        "preloaded_event_ids": [],
    }
    total = client.get(f"{API_PREFIX}/portfolios/laura").json()["total_eur"]
    assert Decimal(total) == LAURA_TOTAL


@pytest.mark.parametrize(
    ("q", "ids"),
    [
        ("iwda", ["IE00B4L5Y983"]),
        ("IE00B03HD191", ["IE00B03HD191"]),
        (
            "vanguard",
            [
                "IE00B03HD191",
                "IE0032126645",
                "IE0007987708",
                "IE0031786142",
                "IE00B18GC888",
                "IE0007472115",
                "IE00BK5BQT80",
                "IE00B3XXRP09",  # VUSA (T4-26)
                "IE00B3RBWM25",  # VWRL (T4-26)
            ],
        ),
        ("zzz", []),
    ],
)
def test_api_lookup_searches_catalog(client: TestClient, q: str, ids: list[str]) -> None:
    body = client.get(f"{API_PREFIX}/assets/lookup", params={"q": q}).json()
    assert sorted(a["id"] for a in body) == sorted(ids)


def test_api_lookup_fills_asset_data(client: TestClient) -> None:
    [asset] = client.get(f"{API_PREFIX}/assets/lookup", params={"q": "IE00B03HD191"}).json()
    assert asset["asset_type"] == "fund"
    assert asset["ter"] == "0.0018"
    assert asset["transferable"] is True
    assert asset["price_kind"] == "nav_daily"
