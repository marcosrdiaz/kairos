"""Casos dorados de compra y venta FIFO (T1-04, RF-04/RF-05) sobre la cartera de Laura.

Los precios son los de `portfolio_init_cases.json`; los valores esperados están en
`portfolio_fifo_cases.json`, calculados aparte.
"""

import json
from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core import clock, trace
from app.core.errors import AppError, ErrorCode
from app.main import API_PREFIX
from app.portfolio import service
from app.schemas.common import TraceKind
from app.schemas.portfolio import TransactionRequest
from tests.fakes.price_provider import FakePriceProvider, use_price_provider

_DIR = Path(__file__).parent
PRICES: dict[str, Any] = json.loads(
    (_DIR / "portfolio_init_cases.json").read_text(encoding="utf-8")
)
CASES: list[dict[str, Any]] = json.loads(
    (_DIR / "portfolio_fifo_cases.json").read_text(encoding="utf-8")
)["cases"]
LOT_FIELDS = ["acquired_at", "units", "cost_eur_per_unit"]


@pytest.fixture(autouse=True)
def _prices() -> Iterator[None]:
    clock.set_now(datetime.fromisoformat(PRICES["now"]))
    with use_price_provider(FakePriceProvider(closes=PRICES["closes"], fx=PRICES["fx"])):
        yield


@pytest.fixture
def seeded(db: None) -> None:
    service.load_seed(force=True)


def _strip_lot_ids(effect: dict[str, Any]) -> dict[str, Any]:
    for key in ("lots_consumed", "lots_created"):
        effect[key] = [{k: lot[k] for k in LOT_FIELDS} for lot in effect[key]]
    return effect


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_operation_matches_golden(seeded: None, case: dict[str, Any]) -> None:
    out = service.register_transaction("laura", TransactionRequest(**case["request"]))
    body = out.model_dump(mode="json")
    expected = case["expected"]
    assert body["type"] == case["request"]["type"]
    assert body["asset_id"] == case["request"]["asset_id"]
    for key in ("units", "price", "price_currency", "fx_rate", "amount_eur"):
        assert body[key] == expected[key], key
    effect = _strip_lot_ids(body["effect"])
    expected_effect = {"lots_created": [], **expected["effect"]}
    assert effect == expected_effect
    assert body["transaction_id"].startswith("tx_")
    assert body["price_at"].startswith("2026-11-06")


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_operation_revalues_portfolio(seeded: None, case: dict[str, Any]) -> None:
    before = service.get_valued("laura")
    out = service.register_transaction("laura", TransactionRequest(**case["request"]))
    asset_id = case["request"]["asset_id"]
    units_after = Decimal(case["expected"]["effect"]["units_after"])
    position = next((p for p in out.portfolio.positions if p.asset_id == asset_id), None)
    if units_after == 0:
        assert position is None
    else:
        assert position is not None
        assert position.units == units_after
    assert out.portfolio.total_eur != before.total_eur or case["request"]["type"] == "buy"
    assert out.portfolio == service.get_valued("laura").model_copy(
        update={"calc_id": out.portfolio.calc_id, "valued_at": out.portfolio.valued_at}
    )


def test_operation_leaves_trace(seeded: None) -> None:
    out = service.register_transaction(
        "laura", TransactionRequest(type="sell", asset_id="IE00B4L5Y983", units=Decimal(80))
    )
    stored = trace.get(out.calc_id)
    assert stored is not None
    assert stored.kind == TraceKind.TRANSACTION
    assert stored.outputs["realized_gain_eur"] == "1588.45"
    assert len(stored.inputs["lots_consumed"]) == 2
    assert {s["kind"] for s in stored.sources} == {"price"}


def test_fifo_continues_after_partial_sale(seeded: None) -> None:
    first = TransactionRequest(type="sell", asset_id="IE00B4L5Y983", units=Decimal(60))
    service.register_transaction("laura", first)
    rest = TransactionRequest(type="sell", asset_id="IE00B4L5Y983", units=Decimal(54))
    out = service.register_transaction("laura", rest)
    consumed = out.effect.lots_consumed
    assert [lot.units for lot in consumed] == [Decimal(10), Decimal(44)]
    assert out.effect.units_after == 0
    # (95,42 − 73,31) × 10 + (95,42 − 91,345) × 44 = 221,10 + 179,30
    assert out.effect.realized_gain_eur == Decimal("400.40")


def test_bought_lot_is_consumed_last(seeded: None) -> None:
    service.register_transaction(
        "laura", TransactionRequest(type="buy", asset_id="IE00B4L5Y983", units=Decimal(6))
    )
    out = service.register_transaction(
        "laura", TransactionRequest(type="sell", asset_id="IE00B4L5Y983", units=Decimal(117))
    )
    assert [lot.units for lot in out.effect.lots_consumed] == [
        Decimal(70),
        Decimal(44),
        Decimal(3),
    ]
    assert out.effect.lots_consumed[-1].cost_eur_per_unit == Decimal("95.42")
    assert out.effect.units_after == Decimal(3)


def test_buy_new_asset_creates_position(seeded: None) -> None:
    out = service.register_transaction(
        "laura", TransactionRequest(type="buy", asset_id="IE0007472115", amount_eur=Decimal(500))
    )
    position = next(p for p in out.portfolio.positions if p.asset_id == "IE0007472115")
    assert position.units == out.units == Decimal("2.11505922")  # 500 / 236,40
    assert position.first_acquired_at == clock.now()


# --- Errores: no cambian nada ---


@pytest.mark.parametrize(
    "request_",
    [
        TransactionRequest(type="sell", asset_id="IE00B4L5Y983", units=Decimal("114.00000001")),
        TransactionRequest(type="sell", asset_id="IE00B4L5Y983", amount_eur=Decimal("10878.89")),
        TransactionRequest(type="sell", asset_id="IE0007472115", units=Decimal(1)),
    ],
    ids=["mas-participaciones", "mas-importe", "sin-posicion"],
)
def test_sell_more_than_held_is_rejected(seeded: None, request_: TransactionRequest) -> None:
    before = service.get_valued("laura").total_eur
    with pytest.raises(AppError) as exc:
        service.register_transaction("laura", request_)
    assert exc.value.code is ErrorCode.INSUFFICIENT_UNITS
    assert exc.value.details["asset_id"] == request_.asset_id
    assert "available_units" in exc.value.details
    assert service.get_valued("laura").total_eur == before


def test_unknown_asset_is_not_found(seeded: None) -> None:
    with pytest.raises(AppError) as exc:
        service.register_transaction(
            "laura", TransactionRequest(type="buy", asset_id="XX0000000000", units=Decimal(1))
        )
    assert exc.value.code is ErrorCode.NOT_FOUND


def test_unknown_portfolio_is_not_found(seeded: None) -> None:
    with pytest.raises(AppError) as exc:
        service.register_transaction(
            "nadie", TransactionRequest(type="buy", asset_id="IE00B4L5Y983", units=Decimal(1))
        )
    assert exc.value.code is ErrorCode.NOT_FOUND


def test_buy_without_price_changes_nothing(seeded: None) -> None:
    before = service.get_valued("laura").total_eur
    with pytest.raises(AppError) as exc:
        service.register_transaction(
            "laura", TransactionRequest(type="buy", asset_id="IE00B5BMR087", units=Decimal(1))
        )
    assert exc.value.code is ErrorCode.PRICE_UNAVAILABLE
    assert service.get_valued("laura").total_eur == before


# --- API ---


def test_api_sell(client: TestClient) -> None:
    body = {"type": "sell", "asset_id": "IE00B4L5Y983", "units": "80"}
    response = client.post(f"{API_PREFIX}/portfolios/laura/transactions", json=body)
    assert response.status_code == 201
    data = response.json()
    assert data["effect"]["realized_gain_eur"] == "1588.45"
    assert data["portfolio"]["id"] == "laura"


def test_api_sell_too_much_is_422(client: TestClient) -> None:
    body = {"type": "sell", "asset_id": "IE00B4L5Y983", "units": "500"}
    response = client.post(f"{API_PREFIX}/portfolios/laura/transactions", json=body)
    assert response.status_code == 422
    assert response.json()["code"] == "INSUFFICIENT_UNITS"
