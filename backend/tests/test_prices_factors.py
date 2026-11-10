"""Series de los 5 factores en directo (T4-01): Yahoo para bolsa, tecnológicas, crudo y EUR/USD;
BCE para los tipos a 10 años. Se guardan en `factor_close` con fecha y fuente. Sin red: los
proveedores son falsos."""

from collections.abc import Iterator
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.core import clock
from app.core.db import session_scope
from app.core.errors import AppError, ErrorCode
from app.prices import factors, service
from app.prices.ecb import parse_rates
from app.prices.models import FactorClose
from app.prices.yahoo import Chart, ProviderError
from app.schemas.common import Factor

NOW = datetime(2026, 11, 10, 15, 0, tzinfo=UTC)  # martes, sesión aún abierta
FRI, MON, TUE = date(2026, 11, 6), date(2026, 11, 9), date(2026, 11, 10)
SAT = date(2026, 11, 7)


class FakeCharts:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.fail = False

    def chart(self, symbol: str, range_: str) -> Chart:
        self.calls.append((symbol, range_))
        if self.fail:
            raise ProviderError(f"{symbol}: sin conexión")
        closes = [
            (FRI, Decimal("100.123456")),
            (SAT, Decimal("1")),  # fin de semana: se descarta
            (MON, Decimal("101.987654")),
            (TUE, Decimal("999")),  # hoy, sesión abierta: se descarta
        ]
        return Chart(
            closes=closes,
            last_price=Decimal("999"),
            last_at=NOW,
            market_open=True,
            next_open=None,
        )


class FakeRates:
    def __init__(self) -> None:
        self.starts: list[date] = []
        self.fail = False

    def rates(self, start: date) -> list[tuple[date, Decimal]]:
        self.starts.append(start)
        if self.fail:
            raise ProviderError("BCE: sin conexión")
        return [
            (FRI, Decimal("0.026234")),
            (MON, Decimal("0.0264701234567")),
            (TUE, Decimal("0.03")),
        ]


@pytest.fixture
def feed(db: None) -> Iterator[tuple[factors.LiveFactors, FakeCharts, FakeRates]]:
    clock.set_now(NOW)
    charts, rates = FakeCharts(), FakeRates()
    live = factors.LiveFactors(charts, rates)
    previous = service.set_factor_source(live)
    yield live, charts, rates
    service.set_factor_source(previous)


def _stored(factor: Factor) -> int:
    with session_scope() as session:
        stmt = select(func.count()).select_from(FactorClose).where(FactorClose.factor == factor)
        return int(session.scalar(stmt) or 0)


# --- BCE ---


def test_parse_ecb_rates_gives_fractions_before_today() -> None:
    text = (
        "KEY,TIME_PERIOD,OBS_VALUE\n"
        "YC.B,2026-11-06,2.6234\n"
        "YC.B,2026-11-07,\n"
        "YC.B,2026-11-09,-0.1\n"
        "YC.B,2026-11-10,2.7\n"
    )
    assert parse_rates(text, TUE) == [(FRI, Decimal("0.026234")), (MON, Decimal("-0.001"))]


# --- En directo ---


def test_live_factors_use_the_symbols_of_fetch_prices(
    feed: tuple[factors.LiveFactors, FakeCharts, FakeRates],
) -> None:
    live, charts, rates = feed
    for factor in Factor:
        live.factor_closes(factor)

    assert sorted(symbol for symbol, _ in charts.calls) == ["BZ=F", "EURUSD=X", "IWDA.AS", "^NDX"]
    assert {range_ for _, range_ in charts.calls} == {"3y"}
    assert rates.starts == [date(2023, 11, 10)]


@pytest.mark.parametrize("factor", list(Factor))
def test_latest_is_the_close_of_the_last_business_day(
    feed: tuple[factors.LiveFactors, FakeCharts, FakeRates], factor: Factor
) -> None:
    latest = service.factor_latest(factor)

    assert latest.day == MON
    assert latest.stale is False
    assert latest.source.as_of == datetime(2026, 11, 9, tzinfo=UTC)
    assert latest.source.ref == factor.value
    assert _stored(factor) == 2


def test_values_are_rounded_like_fetch_prices(
    feed: tuple[factors.LiveFactors, FakeCharts, FakeRates],
) -> None:
    assert service.factor_latest(Factor.OIL).value == Decimal("101.9877")
    assert service.factor_latest(Factor.EURUSD).value == Decimal("101.987654")
    assert service.factor_latest(Factor.RATES_EUR).value == Decimal("0.026470123457")


def test_source_says_where_each_factor_comes_from(
    feed: tuple[factors.LiveFactors, FakeCharts, FakeRates],
) -> None:
    assert "^NDX" in service.factor_latest(Factor.EQ_US_TECH).source.label
    assert "BCE" in service.factor_latest(Factor.RATES_EUR).source.label


def test_refresh_is_cached_and_saving_is_idempotent(
    feed: tuple[factors.LiveFactors, FakeCharts, FakeRates],
) -> None:
    live, charts, _ = feed
    live.factor_closes(Factor.OIL)
    live.factor_closes(Factor.OIL)
    assert len(charts.calls) == 1

    clock.set_now(datetime(2026, 11, 10, 17, 0, tzinfo=UTC))  # pasada la caducidad
    live.factor_closes(Factor.OIL)

    assert charts.calls[-1] == ("BZ=F", "5d")
    assert _stored(Factor.OIL) == 2


def test_provider_failure_serves_the_last_stored_close_marked_stale(
    feed: tuple[factors.LiveFactors, FakeCharts, FakeRates],
) -> None:
    _, charts, rates = feed
    service.factor_latest(Factor.OIL)
    service.factor_latest(Factor.RATES_EUR)

    charts.fail = rates.fail = True
    clock.set_now(datetime(2026, 11, 11, 15, 0, tzinfo=UTC))
    fresh = factors.LiveFactors(charts, rates)  # p. ej. tras reiniciar el backend
    service.set_factor_source(fresh)

    for factor in (Factor.OIL, Factor.RATES_EUR):
        latest = service.factor_latest(factor)
        assert latest.day == MON  # su fecha real, no la de hoy
        assert latest.stale is True
        assert "no respondió" in latest.source.label


def test_provider_failure_without_stored_data_invents_nothing(
    feed: tuple[factors.LiveFactors, FakeCharts, FakeRates],
) -> None:
    _, charts, _ = feed
    charts.fail = True

    with pytest.raises(AppError) as error:
        service.factor_latest(Factor.EQ_GLOBAL)

    assert error.value.code is ErrorCode.PRICE_UNAVAILABLE
    assert _stored(Factor.EQ_GLOBAL) == 0


# --- Offline (modo demo) ---


def test_offline_reads_the_factor_csv(tmp_path: object) -> None:
    from pathlib import Path

    folder = Path(str(tmp_path))
    (folder / "OIL.csv").write_text("date,value\n2025-06-12,69.36\n2025-06-13,74.23\n")
    (folder / "RATES_EUR.csv").write_text("date,value\n2020-03-09,-0.0042\n")
    offline = factors.OfflineFactors(folder)
    previous = service.set_factor_source(offline)
    clock.set_now(datetime(2025, 6, 20, tzinfo=UTC))
    try:
        oil = service.factor_latest(Factor.OIL)
        assert (oil.day, oil.value, oil.stale) == (date(2025, 6, 13), Decimal("74.23"), False)
        assert service.factor_latest(Factor.RATES_EUR).value == Decimal("-0.0042")
        with pytest.raises(AppError):
            service.factor_latest(Factor.EURUSD)  # sin fichero
    finally:
        service.set_factor_source(previous)


def test_offline_default_reads_data_factors() -> None:
    clock.set_now(datetime(2026, 11, 10, tzinfo=UTC))
    latest = factors.OfflineFactors().factor_closes(Factor.EQ_GLOBAL)
    assert latest
    assert latest[-1].day <= date(2026, 11, 10)
