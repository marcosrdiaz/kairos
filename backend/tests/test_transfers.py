"""Traspaso fondo → fondo (T1-05, RF-06) sobre la cartera de Laura.

Precios de `golden/portfolio_init_cases.json` (6-nov-2026). Valores esperados calculados aparte con
`Decimal`: el origen se valora a `price × fx`; cada lote consumido por FIFO abre en el destino un
lote con la misma `acquired_at`, `units = units_consumidas × unit_eur_origen / unit_eur_destino` y
`coste = coste_total_consumido / units` (8 decimales, HALF_EVEN).
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
from app.schemas.portfolio import OperationType, TransactionRequest, TransferRequest
from tests.fakes.price_provider import FakePriceProvider, use_price_provider

PRICES: dict[str, Any] = json.loads(
    (Path(__file__).parent / "golden" / "portfolio_init_cases.json").read_text(encoding="utf-8")
)
VGS = "IE00B03HD191"  # Vanguard Global Stock (fondo), 48,20 €
VGB = "IE00B18GC888"  # Vanguard Global Bond (fondo), 95,10 €
EGB = "IE0007472115"  # Vanguard Euro Government Bond (fondo, sin posición), 236,40 €
US500 = "IE0032126645"  # fondo sin precio en el proveedor de prueba
IWDA = "IE00B4L5Y983"  # ETF
AAPL = "US0378331005"  # acción
ORIGINAL = datetime.fromisoformat("2023-03-06T00:00:00+00:00")


@pytest.fixture(autouse=True)
def _prices() -> Iterator[None]:
    clock.set_now(datetime.fromisoformat(PRICES["now"]))
    with use_price_provider(FakePriceProvider(closes=PRICES["closes"], fx=PRICES["fx"])):
        yield


@pytest.fixture
def seeded(db: None) -> None:
    service.load_seed(force=True)


def _units(portfolio_id: str, asset_id: str) -> Decimal | None:
    positions = service.get_valued(portfolio_id).positions
    return next((p.units for p in positions if p.asset_id == asset_id), None)


# --- Casos dorados ---


def test_transfer_by_units_keeps_date_and_cost(seeded: None) -> None:
    out = service.register_transfer(
        "laura", TransferRequest(from_asset_id=VGS, to_asset_id=VGB, units=Decimal(50))
    )
    assert out.type is OperationType.TRANSFER
    assert (out.asset_id, out.to_asset_id) == (VGS, VGB)
    assert (out.units, out.price, out.price_currency) == (Decimal(50), Decimal("48.20"), "EUR")
    assert out.amount_eur == Decimal("2410.00")
    effect = out.effect
    assert effect.realized_gain_eur is None
    assert (effect.units_after, effect.avg_cost_eur_after) == (
        Decimal("150.31765635"),
        Decimal("36.53"),
    )
    [consumed] = effect.lots_consumed
    assert (consumed.acquired_at, consumed.units) == (ORIGINAL, Decimal(50))
    [created] = effect.lots_created
    assert created.lot_id.startswith("lot_")
    assert created.acquired_at == ORIGINAL
    assert created.units == Decimal("25.34174553")
    assert created.cost_eur_per_unit == Decimal("72.07297531")
    # 50 × 36,5291 = 1826,455 € de coste, conservado a menos de un céntimo
    assert abs(created.units * created.cost_eur_per_unit - Decimal("1826.455")) < Decimal("0.01")
    assert _units("laura", VGB) == Decimal("128.14765654")
    assert _units("laura", VGS) == Decimal("150.31765635")


def test_transfer_by_amount_opens_new_position(seeded: None) -> None:
    out = service.register_transfer(
        "laura", TransferRequest(from_asset_id=VGS, to_asset_id=EGB, amount_eur=Decimal(1000))
    )
    assert (out.units, out.amount_eur) == (Decimal("20.74688797"), Decimal("1000.00"))
    assert out.effect.units_after == Decimal("179.57076838")
    [created] = out.effect.lots_created
    assert (created.units, created.cost_eur_per_unit) == (
        Decimal("4.23011844"),
        Decimal("179.15932050"),
    )
    position = next(p for p in out.portfolio.positions if p.asset_id == EGB)
    assert position.units == Decimal("4.23011844")
    assert position.first_acquired_at == ORIGINAL  # conserva la antigüedad


def test_full_transfer_closes_origin(seeded: None) -> None:
    out = service.register_transfer(
        "laura",
        TransferRequest(from_asset_id=VGB, to_asset_id=VGS, units=Decimal("102.80591101")),
    )
    assert out.amount_eur == Decimal("9776.84")
    assert (out.effect.units_after, out.effect.avg_cost_eur_after) == (Decimal(0), Decimal(0))
    [created] = out.effect.lots_created
    assert (created.units, created.cost_eur_per_unit) == (
        Decimal("202.83904849"),
        Decimal("46.73940315"),
    )
    assert all(p.asset_id != VGB for p in out.portfolio.positions)


def test_transfer_consuming_two_lots_creates_two(seeded: None) -> None:
    service.register_transaction(
        "laura", TransactionRequest(type="buy", asset_id=VGS, units=Decimal(10))
    )
    out = service.register_transfer(
        "laura", TransferRequest(from_asset_id=VGS, to_asset_id=VGB, units=Decimal(205))
    )
    assert [lot.units for lot in out.effect.lots_consumed] == [
        Decimal("200.31765635"),
        Decimal("4.68234365"),
    ]
    created = out.effect.lots_created
    assert [lot.acquired_at for lot in created] == [ORIGINAL, clock.now()]
    assert [lot.units for lot in created] == [Decimal("101.52798145"), Decimal("2.37317523")]
    assert [lot.cost_eur_per_unit for lot in created] == [
        Decimal("72.07297531"),
        Decimal("95.09999981"),
    ]
    assert (out.effect.units_after, out.effect.avg_cost_eur_after) == (
        Decimal("5.31765635"),
        Decimal("48.20"),
    )


def test_transfer_keeps_portfolio_value(seeded: None) -> None:
    before = service.get_valued("laura").total_eur
    out = service.register_transfer(
        "laura", TransferRequest(from_asset_id=VGS, to_asset_id=VGB, units=Decimal(50))
    )
    assert abs(out.portfolio.total_eur - before) <= Decimal("0.01")


def test_transfer_leaves_trace(seeded: None) -> None:
    out = service.register_transfer(
        "laura", TransferRequest(from_asset_id=VGS, to_asset_id=VGB, units=Decimal(50))
    )
    stored = trace.get(out.calc_id)
    assert stored is not None
    assert stored.kind == TraceKind.TRANSFER
    assert stored.outputs["amount_eur"] == "2410.00"
    assert stored.outputs["to_units"] == "25.34174553"
    assert len(stored.inputs["lots_consumed"]) == 1
    assert {s["kind"] for s in stored.sources} == {"price"}


def test_transfer_is_neutral_in_value_change(seeded: None) -> None:
    start = clock.now()
    clock.set_now(datetime.fromisoformat("2026-11-08T19:00:00+00:00"))
    service.register_transfer(
        "laura", TransferRequest(from_asset_id=VGS, to_asset_id=VGB, units=Decimal(50))
    )
    change = service.get_value_change("laura", start, clock.now())
    assert change.net_flows_eur == Decimal(0)


# --- Errores: no cambian nada ---


@pytest.mark.parametrize(
    ("from_id", "to_id", "types"),
    [(IWDA, VGS, ("etf", "fund")), (VGS, AAPL, ("fund", "stock"))],
    ids=["etf-a-fondo", "fondo-a-accion"],
)
def test_non_fund_is_not_allowed(
    seeded: None, from_id: str, to_id: str, types: tuple[str, str]
) -> None:
    before = service.get_valued("laura").total_eur
    with pytest.raises(AppError) as exc:
        service.register_transfer(
            "laura", TransferRequest(from_asset_id=from_id, to_asset_id=to_id, units=Decimal(1))
        )
    error = exc.value
    assert error.code is ErrorCode.TRANSFER_NOT_ALLOWED
    assert (error.details["from_asset_type"], error.details["to_asset_type"]) == types
    assert error.details["alternative"] == "sell_and_buy"
    assert "tributa" in error.message
    assert service.get_valued("laura").total_eur == before


def test_not_allowed_estimates_gain_of_selling(seeded: None) -> None:
    with pytest.raises(AppError) as exc:
        service.register_transfer(
            "laura", TransferRequest(from_asset_id=IWDA, to_asset_id=VGS, units=Decimal(50))
        )
    details = exc.value.details
    # 50 × 95,42 − 50 × 73,31 (primer lote, FIFO)
    assert details["estimated_gain_eur"] == "1105.50"
    stored = trace.get(details["calc_id"])
    assert stored is not None
    assert stored.kind == TraceKind.TRANSFER


def test_not_allowed_without_enough_units_has_no_estimate(seeded: None) -> None:
    with pytest.raises(AppError) as exc:
        service.register_transfer(
            "laura", TransferRequest(from_asset_id=IWDA, to_asset_id=VGS, units=Decimal(500))
        )
    assert exc.value.code is ErrorCode.TRANSFER_NOT_ALLOWED
    assert exc.value.details["estimated_gain_eur"] is None
    assert exc.value.details["calc_id"] is None


def test_same_fund_is_rejected(seeded: None) -> None:
    with pytest.raises(AppError) as exc:
        service.register_transfer(
            "laura", TransferRequest(from_asset_id=VGS, to_asset_id=VGS, units=Decimal(1))
        )
    assert exc.value.code is ErrorCode.VALIDATION_ERROR


def test_more_than_held_is_rejected(seeded: None) -> None:
    before = _units("laura", VGS)
    with pytest.raises(AppError) as exc:
        service.register_transfer(
            "laura",
            TransferRequest(from_asset_id=VGS, to_asset_id=VGB, units=Decimal("200.31765636")),
        )
    assert exc.value.code is ErrorCode.INSUFFICIENT_UNITS
    assert exc.value.details["asset_id"] == VGS
    assert _units("laura", VGS) == before


def test_destination_without_price_changes_nothing(seeded: None) -> None:
    before = _units("laura", VGS)
    with pytest.raises(AppError) as exc:
        service.register_transfer(
            "laura", TransferRequest(from_asset_id=VGS, to_asset_id=US500, units=Decimal(1))
        )
    assert exc.value.code is ErrorCode.PRICE_UNAVAILABLE
    assert _units("laura", VGS) == before


@pytest.mark.parametrize(("portfolio_id", "from_id"), [("nadie", VGS), ("laura", "XX0000000000")])
def test_unknown_portfolio_or_asset_is_not_found(
    seeded: None, portfolio_id: str, from_id: str
) -> None:
    with pytest.raises(AppError) as exc:
        service.register_transfer(
            portfolio_id, TransferRequest(from_asset_id=from_id, to_asset_id=VGB, units=Decimal(1))
        )
    assert exc.value.code is ErrorCode.NOT_FOUND


# --- API ---


def test_api_transfer(client: TestClient) -> None:
    body = {"from_asset_id": VGS, "to_asset_id": VGB, "units": "50"}
    response = client.post(f"{API_PREFIX}/portfolios/laura/transfers", json=body)
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "transfer"
    assert data["to_asset_id"] == VGB
    assert data["effect"]["realized_gain_eur"] is None
    assert data["effect"]["lots_created"][0]["acquired_at"] == "2023-03-06T00:00:00Z"


def test_api_etf_transfer_is_422(client: TestClient) -> None:
    body = {"from_asset_id": IWDA, "to_asset_id": VGS, "units": "50"}
    response = client.post(f"{API_PREFIX}/portfolios/laura/transfers", json=body)
    assert response.status_code == 422
    error = response.json()
    assert error["code"] == "TRANSFER_NOT_ALLOWED"
    assert error["details"]["from_asset_type"] == "etf"
    assert error["details"]["estimated_gain_eur"] == "1105.50"
