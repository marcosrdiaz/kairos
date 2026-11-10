"""Actualización diaria tras el cierre (T4-02): `scripts/daily_update.py`.

Sin red: Yahoo y el BCE son falsos. Los cierres se guardan con el proveedor en directo de T2-24
(`price`, `fx_rate`) y la fuente de factores de T4-01 (`factor_close`).
"""

import importlib.util
import sys
from collections.abc import Iterator
from datetime import UTC, date, datetime, time
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core import clock
from app.core.db import session_scope
from app.portfolio import service as portfolio_service
from app.prices import factors
from app.prices import service as prices_service
from app.prices.live import LiveProvider
from app.prices.models import FactorClose, FxRate, Price
from app.prices.yahoo import Chart, ProviderError

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "daily_update.py"
NOW = datetime(2026, 11, 10, 22, 30, tzinfo=UTC)  # martes, tras el cierre de EE. UU.
MON = date(2026, 11, 9)
FAILING = "NVDA"


@pytest.fixture(scope="module")
def daily_update() -> ModuleType:
    spec = importlib.util.spec_from_file_location("daily_update", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["daily_update"] = module
    spec.loader.exec_module(module)
    return module


class FakeCharts:
    def __init__(self) -> None:
        self.fail: set[str] = set()

    def chart(self, symbol: str, range_: str) -> Chart:
        if symbol in self.fail:
            raise ProviderError(f"{symbol}: sin conexión")
        return Chart(
            closes=[(date(2026, 11, 6), Decimal("10")), (MON, Decimal("11"))],
            last_price=None,
            last_at=None,
            market_open=False,
            next_open=None,
        )


class FakeRates:
    def __init__(self) -> None:
        self.fail = False

    def rates(self, start: date) -> list[tuple[date, Decimal]]:
        if self.fail:
            raise ProviderError("BCE: sin conexión")
        return [(MON, Decimal("0.0265"))]


@pytest.fixture
def live(client: TestClient) -> Iterator[tuple[FakeCharts, FakeRates]]:
    clock.set_now(NOW)
    charts, rates = FakeCharts(), FakeRates()
    previous_prices = prices_service.set_provider(LiveProvider(charts))
    previous_factors = prices_service.set_factor_source(factors.LiveFactors(charts, rates))
    yield charts, rates
    prices_service.set_provider(previous_prices)
    prices_service.set_factor_source(previous_factors)


def _count(model: Any) -> int:
    with session_scope() as session:
        return int(session.scalar(select(func.count()).select_from(model)) or 0)


# --- Qué se actualiza ---


def test_held_asset_ids_are_those_of_every_portfolio(client: TestClient) -> None:
    held = portfolio_service.held_asset_ids()

    assert "US67066G1040" in held  # NVIDIA (Laura)
    assert held == sorted(held)
    assert len(held) == len(set(held))


def test_held_asset_ids_without_portfolios_is_empty(db: None) -> None:
    portfolio_service.load_seed(portfolios=False)
    assert portfolio_service.held_asset_ids() == []


def test_update_saves_last_close_of_assets_fx_and_factors(
    daily_update: ModuleType, live: tuple[FakeCharts, FakeRates]
) -> None:
    report = daily_update.update_once()

    assert report.failed == {}
    market = [a for a in portfolio_service.held_asset_ids() if prices_service.has_market_prices(a)]
    assert sorted(report.updated) == sorted(
        [f"asset:{a}" for a in market]
        + ["fx:EURUSD"]
        + [f"factor:{f.value}" for f in factors.YAHOO_FACTORS]
        + ["factor:RATES_EUR"]
    )
    with session_scope() as session:
        days = set(session.scalars(select(FactorClose.day)))
    assert MON in days
    with session_scope() as session:  # el recálculo semanal de betas (T4-03) pide el resto
        held_rows = session.scalar(
            select(func.count()).select_from(Price).where(Price.asset_id.in_(market))
        )
    assert held_rows == 2 * len(market)
    assert _count(FxRate) == 2
    assert _count(FactorClose) == 2 * 4 + 1


def test_running_twice_does_not_duplicate_rows(
    daily_update: ModuleType, live: tuple[FakeCharts, FakeRates]
) -> None:
    daily_update.update_once()
    counts = (_count(Price), _count(FxRate), _count(FactorClose))

    clock.set_now(datetime(2026, 11, 11, 22, 30, tzinfo=UTC))  # pasada la caducidad
    daily_update.update_once()

    assert (_count(Price), _count(FxRate), _count(FactorClose)) == counts


def test_failures_are_reported_and_the_rest_is_saved(
    daily_update: ModuleType, live: tuple[FakeCharts, FakeRates]
) -> None:
    charts, rates = live
    charts.fail = {FAILING, "BZ=F"}
    rates.fail = True

    report = daily_update.update_once()

    assert set(report.failed) == {"asset:US67066G1040", "factor:OIL", "factor:RATES_EUR"}
    assert all(report.failed.values())
    assert "asset:IE00B4L5Y983" in report.updated  # iShares MSCI World (en cartera)


def test_betas_are_recomputed_weekly_after_saving_the_closes(
    daily_update: ModuleType,
    live: tuple[FakeCharts, FakeRates],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.impact import service as impact_service

    calls: list[int] = []

    def fake_if_due() -> impact_service.BetaRun | None:
        calls.append(_count(FactorClose))  # los cierres ya están guardados
        return impact_service.BetaRun(computed_at=NOW, estimated=["IE00B4L5Y983"])

    monkeypatch.setattr(impact_service, "recompute_betas_if_due", fake_if_due)
    report = daily_update.update_once()

    assert calls == [2 * 4 + 1]
    assert report.betas == ["IE00B4L5Y983"]
    assert "betas" not in report.failed


def test_a_failed_beta_recompute_is_reported(
    daily_update: ModuleType,
    live: tuple[FakeCharts, FakeRates],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.impact import service as impact_service

    def boom() -> None:
        raise RuntimeError("sin datos")

    monkeypatch.setattr(impact_service, "recompute_betas_if_due", boom)
    report = daily_update.update_once()

    assert report.failed["betas"] == "sin datos"
    assert report.betas is None


def test_a_stale_value_counts_as_a_failure(
    daily_update: ModuleType, live: tuple[FakeCharts, FakeRates]
) -> None:
    charts, _ = live
    daily_update.update_once()

    charts.fail = {"BZ=F"}
    clock.set_now(datetime(2026, 11, 11, 22, 30, tzinfo=UTC))
    report = daily_update.update_once()

    assert "factor:OIL" in report.failed
    assert "no respondió" in report.failed["factor:OIL"]


# --- Cuándo ---


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        (datetime(2026, 11, 10, 10, 0, tzinfo=UTC), datetime(2026, 11, 10, 22, 30, tzinfo=UTC)),
        (datetime(2026, 11, 10, 22, 30, tzinfo=UTC), datetime(2026, 11, 11, 22, 30, tzinfo=UTC)),
        (datetime(2026, 11, 13, 23, 0, tzinfo=UTC), datetime(2026, 11, 16, 22, 30, tzinfo=UTC)),
        (datetime(2026, 11, 14, 9, 0, tzinfo=UTC), datetime(2026, 11, 16, 22, 30, tzinfo=UTC)),
    ],
)
def test_next_run_is_the_next_weekday_after_the_close(
    daily_update: ModuleType, now: datetime, expected: datetime
) -> None:
    assert daily_update.next_run(now, time(22, 30)) == expected


def test_demo_mode_does_nothing(daily_update: ModuleType, db: None) -> None:
    assert daily_update.main(["--once"]) == 0


def test_parse_at(daily_update: ModuleType) -> None:
    assert daily_update.parse_at("21:15") == time(21, 15)
    with pytest.raises(ValueError):
        daily_update.parse_at("25:00")
