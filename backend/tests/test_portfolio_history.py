"""Evolución del valor de la cartera (T2-18): muestreo, valoración por fecha y endpoint."""

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
from app.portfolio import history, service
from app.schemas.history import HistoryPeriod
from app.schemas.portfolio import TransactionRequest
from tests.fakes.price_provider import FakePriceProvider, use_price_provider

CASES: dict[str, Any] = json.loads(
    (Path(__file__).parent / "golden" / "portfolio_init_cases.json").read_text(encoding="utf-8")
)
NOW = datetime.fromisoformat(CASES["now"])  # domingo 2026-11-08T18:00:00Z
D = Decimal
MSCI_EUR = "IE00B03HD191"


@pytest.fixture(autouse=True)
def _prices() -> Iterator[None]:
    clock.set_now(NOW)
    with use_price_provider(FakePriceProvider(closes=CASES["closes"], fx=CASES["fx"])):
        yield


@pytest.fixture
def seeded(db: None) -> None:
    service.load_seed(force=True)


# --- Muestreo (puro) ---


def test_one_month_is_every_weekday_since_the_same_day_last_month() -> None:
    days = history.sample_days(date(2026, 11, 6), HistoryPeriod.ONE_MONTH, date(2020, 1, 1))
    assert days[0] == date(2026, 10, 6)
    assert days[-1] == date(2026, 11, 6)
    assert all(d.weekday() < 5 for d in days)
    assert len(days) == 24  # 4 en la semana del 6-oct y 5 en cada una de las 4 siguientes


def test_start_never_goes_before_the_first_operation() -> None:
    days = history.sample_days(date(2026, 11, 6), HistoryPeriod.ONE_YEAR, date(2026, 11, 2))
    assert days == [date(2026, 11, d) for d in (2, 3, 4, 5, 6)]


def test_max_is_weekly_back_from_the_last_day() -> None:
    days = history.sample_days(date(2026, 11, 6), HistoryPeriod.MAX, date(2026, 10, 10))
    assert days == [date(2026, 10, 16), date(2026, 10, 23), date(2026, 10, 30), date(2026, 11, 6)]


def test_end_on_a_weekend_moves_back_to_friday() -> None:
    days = history.sample_days(date(2026, 11, 8), HistoryPeriod.ONE_MONTH, date(2020, 1, 1))
    assert days[-1] == date(2026, 11, 6)


def test_three_and_six_months_and_one_year_start_on_the_same_day() -> None:
    end, first = date(2026, 11, 6), date(2020, 1, 1)
    assert history.sample_days(end, HistoryPeriod.THREE_MONTHS, first)[0] == date(2026, 8, 6)
    assert history.sample_days(end, HistoryPeriod.SIX_MONTHS, first)[0] == date(2026, 5, 6)
    assert history.sample_days(end, HistoryPeriod.ONE_YEAR, first)[0] == date(2025, 11, 6)


# --- Último cierre y valor de un día (puro) ---

SERIES = [(date(2026, 10, 30), D("10")), (date(2026, 11, 6), D("12"))]


def test_last_close_on_or_before_the_day() -> None:
    assert history.last_close(SERIES, date(2026, 11, 2)) == D("10")
    assert history.last_close(SERIES, date(2026, 11, 6)) == D("12")


def test_last_close_is_none_before_the_series_or_when_too_old() -> None:
    assert history.last_close(SERIES, date(2026, 10, 29)) is None
    assert history.last_close(SERIES, date(2026, 11, 17)) is None


def test_day_value_sums_assets_rounded_to_cents() -> None:
    units = {"A": D("3"), "B": D("1.5")}
    assert history.day_value(units, {"A": D("10.005"), "B": D("2")}) == D("33.02")


def test_day_value_is_none_if_an_asset_has_no_price() -> None:
    assert history.day_value({"A": D("1"), "B": D("1")}, {"A": D("10"), "B": None}) is None


def test_day_value_is_none_without_holdings() -> None:
    assert history.day_value({}, {}) is None


# --- get_history con la cartera del seed ---


def test_series_skips_days_without_price_and_ends_at_the_current_value(seeded: None) -> None:
    out = history.get_history("laura", HistoryPeriod.ONE_MONTH)
    days = [p.date.date() for p in out.points]
    assert days[0] == date(2026, 10, 30)  # antes no hay cierres en el proveedor falso
    assert days[-1] == date(2026, 11, 6)
    valued = service.get_valued("laura")
    assert out.end_value_eur == out.points[-1].value_eur == valued.total_eur
    assert out.start_value_eur == valued.total_eur - valued.change_week_eur
    assert out.net_flows_eur == D("0.00")
    assert all(p.date.tzinfo == UTC for p in out.points)


def test_a_buy_inside_the_period_is_a_flow(seeded: None) -> None:
    clock.set_now(datetime(2026, 11, 3, 12, tzinfo=UTC))
    service.register_transaction(
        "laura", TransactionRequest(type="buy", asset_id=MSCI_EUR, amount_eur=D("300.00"))
    )
    clock.set_now(NOW)
    out = history.get_history("laura", HistoryPeriod.ONE_MONTH)
    assert out.net_flows_eur == D("300.00")
    assert out.end_value_eur == service.get_valued("laura").total_eur


def test_series_is_traced(seeded: None) -> None:
    out = history.get_history("laura", HistoryPeriod.ONE_MONTH)
    record = trace.get(out.calc_id)
    assert record is not None
    assert record.kind == "valuation"
    assert record.outputs["end_value_eur"] == format(out.end_value_eur, "f")
    assert len(record.outputs["points"]) == len(out.points)
    assert out.sources and record.sources


def test_unknown_portfolio(db: None) -> None:
    with pytest.raises(AppError) as error:
        history.get_history("nadie", HistoryPeriod.ONE_MONTH)
    assert error.value.code == ErrorCode.NOT_FOUND


def test_no_prices_in_the_period_is_price_unavailable(seeded: None) -> None:
    with use_price_provider(FakePriceProvider()), pytest.raises(AppError) as error:
        history.get_history("laura", HistoryPeriod.ONE_MONTH)
    assert error.value.code == ErrorCode.PRICE_UNAVAILABLE


def test_endpoint(client: TestClient, seeded: None) -> None:
    response = client.get(f"{API_PREFIX}/portfolios/laura/history", params={"period": "1m"})
    assert response.status_code == 200
    body = response.json()
    assert body["period"] == "1m"
    assert body["points"][-1]["date"] == "2026-11-06T00:00:00Z"
    assert body["end_value_eur"] == body["points"][-1]["value_eur"]
    assert client.get(f"{API_PREFIX}/portfolios/nadie/history").status_code == 404


def test_endpoint_period_defaults_to_one_year(client: TestClient, seeded: None) -> None:
    response = client.get(f"{API_PREFIX}/portfolios/laura/history")
    assert response.json()["period"] == "1y"


def test_endpoint_rejects_an_unknown_period(client: TestClient, seeded: None) -> None:
    response = client.get(f"{API_PREFIX}/portfolios/laura/history", params={"period": "2w"})
    assert response.status_code == 422
