"""Ticker de mercado (T2-17): variación frente al cierre anterior, con proveedor falso."""

from collections.abc import Iterator
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.core import clock, trace
from app.prices import service
from app.prices.ticker import change_pct
from tests.fakes.price_provider import FakePriceProvider, use_price_provider

IWDA = "IE00B4L5Y983"  # ETF en EUR
APPLE = "US0378331005"  # acción en USD, un solo cierre
DEPOSIT = "DEP-12M"  # fixed:1

NOW = datetime(2026, 11, 8, 18, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _fake() -> Iterator[None]:
    clock.set_now(NOW)
    provider = FakePriceProvider(
        closes={
            IWDA: {"2026-11-04": "94.00", "2026-11-05": "95.10", "2026-11-06": "95.42"},
            APPLE: {"2026-11-06": "228.10"},
        },
    )
    with use_price_provider(provider):
        yield


# --- Función pura ---


def test_change_is_a_fraction_of_the_previous_price() -> None:
    assert change_pct(Decimal("95.42"), Decimal("95.10")) == Decimal("0.003365")


def test_a_fall_is_negative() -> None:
    assert change_pct(Decimal("90"), Decimal("100")) == Decimal("-0.100000")


def test_rounds_half_even_to_six_decimals() -> None:
    # 0.0000005 → 0.000000 y 0.0000015 → 0.000002: el empate va al par
    assert change_pct(Decimal("1.0000005"), Decimal("1")) == Decimal("0.000000")
    assert change_pct(Decimal("1.0000015"), Decimal("1")) == Decimal("0.000002")


def test_no_previous_price_means_no_change() -> None:
    assert change_pct(Decimal("10"), None) is None


def test_a_zero_previous_price_means_no_change() -> None:
    assert change_pct(Decimal("10"), Decimal("0")) is None


# --- `prices.service.previous_close` ---


def test_previous_close_is_the_last_one_before_the_day() -> None:
    previous = service.previous_close(IWDA, date(2026, 11, 6))

    assert previous is not None
    assert previous.price == Decimal("95.10")
    assert previous.price_at == datetime(2026, 11, 5, tzinfo=UTC)


def test_previous_close_is_none_with_a_single_close() -> None:
    assert service.previous_close(APPLE, date(2026, 11, 6)) is None


def test_previous_close_is_none_for_a_fixed_price() -> None:
    assert service.previous_close(DEPOSIT, date(2026, 11, 8)) is None


# --- `prices.service.ticker_item` ---


@pytest.mark.usefixtures("db")
def test_item_has_both_closes_change_and_trace() -> None:
    item = service.ticker_item(IWDA, ticker="IWDA", name="iShares Core MSCI World")

    assert item.price == Decimal("95.42")
    assert item.price_at == datetime(2026, 11, 6, tzinfo=UTC)
    assert item.previous_price == Decimal("95.10")
    assert item.previous_price_at == datetime(2026, 11, 5, tzinfo=UTC)
    assert item.change_pct == Decimal("0.003365")
    record = trace.get(item.calc_id)
    assert record is not None
    assert record.outputs["change_pct"] == "0.003365"
    assert record.inputs["price"] == "95.42"
    assert record.inputs["previous_price"] == "95.10"
    assert [s["ref"] for s in record.sources] == [IWDA, IWDA]
    assert [s["as_of"] for s in record.sources] == ["2026-11-06T00:00:00Z", "2026-11-05T00:00:00Z"]


@pytest.mark.usefixtures("db")
def test_item_without_previous_close_has_no_change() -> None:
    item = service.ticker_item(APPLE, ticker="AAPL", name="Apple")

    assert item.previous_price is None
    assert item.previous_price_at is None
    assert item.change_pct is None
    assert trace.get(item.calc_id) is not None


@pytest.mark.usefixtures("db")
def test_item_with_fixed_price_has_no_change() -> None:
    item = service.ticker_item(DEPOSIT, ticker=None, name="Depósito")

    assert item.price == Decimal("1")
    assert item.change_pct is None
