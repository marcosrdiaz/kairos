"""Evolución de una posición (T2-23): `asset_history.get_asset_history` y su endpoint."""

import json
from collections.abc import Iterator
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core import clock, trace
from app.core.errors import AppError, ErrorCode
from app.main import API_PREFIX
from app.portfolio import asset_history, service
from app.schemas.history import HistoryPeriod
from app.schemas.portfolio import TransactionRequest
from tests.fakes.price_provider import FakePriceProvider, use_price_provider

CASES: dict[str, Any] = json.loads(
    (Path(__file__).parent / "golden" / "portfolio_init_cases.json").read_text(encoding="utf-8")
)
NOW = datetime.fromisoformat(CASES["now"])  # domingo 2026-11-08T18:00:00Z
D = Decimal
NVDA = "US67066G1040"  # 8 participaciones de Laura, en USD
MSCI_EUR = "IE00B03HD191"  # fondo de Laura y de Javier, en EUR


@pytest.fixture(autouse=True)
def _prices() -> Iterator[None]:
    clock.set_now(NOW)
    with use_price_provider(FakePriceProvider(closes=CASES["closes"], fx=CASES["fx"])):
        yield


@pytest.fixture
def seeded(db: None) -> None:
    service.load_seed(force=True)


def _position_value(portfolio_id: str, asset_id: str) -> Decimal:
    valued = service.get_valued(portfolio_id)
    return next(p.value_eur for p in valued.positions if p.asset_id == asset_id)


def test_series_of_a_usd_position(seeded: None) -> None:
    out = asset_history.get_asset_history("laura", NVDA, HistoryPeriod.ONE_MONTH)

    assert (out.portfolio_id, out.asset_id, out.period) == ("laura", NVDA, HistoryPeriod.ONE_MONTH)
    assert out.currency == "USD"
    assert out.name
    assert [p.date.date() for p in out.points] == [date(2026, 10, 30), date(2026, 11, 6)]
    first, last = out.points
    # Precio en la divisa del activo; valor en euros con el fx de ese día.
    assert (first.price, last.price) == (D("180.00"), D("182.50"))
    assert first.units == last.units == D("8")
    assert first.value_eur == D("1252.17")  # 8 × 180 / 1,15
    assert last.value_eur == out.end_value_eur == _position_value("laura", NVDA)
    assert out.start_value_eur == first.value_eur
    assert last.change_eur == last.value_eur - first.value_eur
    assert out.net_flows_eur == D("0.00")
    assert all(p.date.tzinfo == UTC for p in out.points)


def test_only_this_asset_flows_count(seeded: None) -> None:
    clock.set_now(datetime(2026, 11, 3, 12, tzinfo=UTC))
    service.register_transaction(
        "laura", TransactionRequest(type="buy", asset_id=MSCI_EUR, amount_eur=D("300.00"))
    )
    clock.set_now(NOW)

    nvda = asset_history.get_asset_history("laura", NVDA, HistoryPeriod.ONE_MONTH)
    msci = asset_history.get_asset_history("laura", MSCI_EUR, HistoryPeriod.ONE_MONTH)

    assert nvda.net_flows_eur == D("0.00")
    assert msci.net_flows_eur == D("300.00")
    assert [p.flows_eur for p in msci.points] == [D("0.00"), D("300.00")]
    assert msci.points[-1].units > msci.points[0].units
    assert msci.end_value_eur == _position_value("laura", MSCI_EUR)


def test_a_sold_position_keeps_its_price_with_zero_value(seeded: None) -> None:
    clock.set_now(datetime(2026, 11, 3, 12, tzinfo=UTC))
    service.register_transaction(
        "laura", TransactionRequest(type="sell", asset_id=NVDA, units=D("8"))
    )
    clock.set_now(NOW)

    out = asset_history.get_asset_history("laura", NVDA, HistoryPeriod.ONE_MONTH)

    last = out.points[-1]
    assert last.units == D("0")
    assert last.value_eur == D("0.00")
    assert last.price == D("182.50")
    assert last.flows_eur < 0  # la venta es dinero que sale


def test_series_starts_at_the_first_operation_of_the_asset(seeded: None) -> None:
    clock.set_now(datetime(2026, 11, 3, 12, tzinfo=UTC))
    service.register_transaction(
        "javier", TransactionRequest(type="buy", asset_id=NVDA, units=D("1"))
    )
    clock.set_now(NOW)

    out = asset_history.get_asset_history("javier", NVDA, HistoryPeriod.ONE_MONTH)

    assert [p.date.date() for p in out.points] == [date(2026, 11, 6)]
    assert out.points[0].units == D("1")


def test_series_is_traced(seeded: None) -> None:
    out = asset_history.get_asset_history("laura", NVDA, HistoryPeriod.ONE_MONTH)
    record = trace.get(out.calc_id)
    assert record is not None
    assert record.kind == "valuation"
    assert record.inputs["asset_id"] == NVDA
    assert record.outputs["end_value_eur"] == format(out.end_value_eur, "f")
    assert len(record.outputs["points"]) == len(out.points)
    assert out.sources and record.sources


def test_unknown_portfolio(db: None) -> None:
    with pytest.raises(AppError) as error:
        asset_history.get_asset_history("nadie", NVDA, HistoryPeriod.ONE_MONTH)
    assert error.value.code == ErrorCode.NOT_FOUND


def test_asset_never_held_is_not_found(seeded: None) -> None:
    with pytest.raises(AppError) as error:
        asset_history.get_asset_history("javier", NVDA, HistoryPeriod.ONE_MONTH)
    assert error.value.code == ErrorCode.NOT_FOUND


def test_no_prices_in_the_period_is_price_unavailable(seeded: None) -> None:
    with use_price_provider(FakePriceProvider()), pytest.raises(AppError) as error:
        asset_history.get_asset_history("laura", NVDA, HistoryPeriod.ONE_MONTH)
    assert error.value.code == ErrorCode.PRICE_UNAVAILABLE


def test_endpoint(client: TestClient, seeded: None) -> None:
    url = f"{API_PREFIX}/portfolios/laura/positions/{NVDA}/history"
    response = client.get(url, params={"period": "1m"})
    assert response.status_code == 200
    body = response.json()
    assert body["asset_id"] == NVDA
    assert body["points"][-1]["date"] == "2026-11-06T00:00:00Z"
    assert body["points"][-1]["price"] == "182.50000000"
    assert body["end_value_eur"] == body["points"][-1]["value_eur"]
    point = body["points"][0]
    assert {"date", "value_eur", "flows_eur", "price", "units"} <= point.keys()
    assert body["calc_id"].startswith("calc_")
    missing = f"{API_PREFIX}/portfolios/javier/positions/{NVDA}/history"
    assert client.get(missing).status_code == 404


def test_endpoint_period_defaults_to_one_year(client: TestClient, seeded: None) -> None:
    url = f"{API_PREFIX}/portfolios/laura/positions/{NVDA}/history"
    assert client.get(url).json()["period"] == "1y"


def test_endpoint_rejects_an_unknown_period(client: TestClient, seeded: None) -> None:
    url = f"{API_PREFIX}/portfolios/laura/positions/{NVDA}/history"
    assert client.get(url, params={"period": "2w"}).status_code == 422
