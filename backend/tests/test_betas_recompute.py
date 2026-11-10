"""Betas recalculadas solas (T4-03): `impact.service.recompute_betas` lee las series de `prices`
(el proveedor activo: CSV en demo, BD en directo), guarda `computed_at` y se repite cada semana."""

from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import numpy as np
import pytest

from app.core import clock
from app.core.db import session_scope
from app.impact import repository
from app.impact import service as impact_service
from app.portfolio.models import Asset
from app.prices import service as prices_service
from app.prices.provider import PricePoint
from app.schemas.common import Factor
from tests.fakes.price_provider import FakePriceProvider, use_price_provider

NOW = datetime(2026, 11, 6, 18, 0, tzinfo=UTC)
ETF = "IE00B4L5Y983"
STOCK = "US67066G1040"
FUND = "IE00B03HD191"
DEPOSIT = "DEP-12M"
N_DAYS = 300
START = date(2025, 8, 1)


def _days() -> list[date]:
    return [START + timedelta(days=i) for i in range(N_DAYS + 1)]


def _levels(start: float, returns: np.ndarray) -> list[Decimal]:
    levels = [start]
    for r in returns:
        levels.append(levels[-1] * (1 + float(r)))
    return [Decimal(repr(round(v, 8))) for v in levels]


class _Factors:
    def __init__(self, series: dict[Factor, list[PricePoint]]) -> None:
        self._series = series

    def factor_closes(self, factor: Factor) -> list[PricePoint]:
        return list(self._series.get(factor, []))

    def source_of(self, factor: Factor, day: date) -> str | None:
        return "csv:test"


class _AdjustedProvider(FakePriceProvider):
    """Proveedor que además da cierres ajustados por dividendos (como los CSV de `data/prices`)."""

    def __init__(self, adjusted: dict[str, list[PricePoint]], **kwargs: object) -> None:
        super().__init__(**kwargs)  # type: ignore[arg-type]
        self._adjusted = adjusted

    def adjusted_closes(self, asset_id: str) -> list[PricePoint]:
        return list(self._adjusted.get(asset_id, []))


def _market(
    seed: int = 3,
) -> tuple[dict[Factor, list[PricePoint]], np.ndarray, dict[Factor, np.ndarray]]:
    rng = np.random.default_rng(seed)
    moves = {f: rng.normal(0, 0.01, N_DAYS) for f in Factor}
    moves[Factor.RATES_EUR] = rng.normal(0, 0.0005, N_DAYS)
    days = _days()
    series: dict[Factor, list[PricePoint]] = {}
    for f, m in moves.items():
        if f is Factor.RATES_EUR:
            values = [Decimal(repr(round(float(v), 10))) for v in 0.025 + np.cumsum([0.0, *m])]
        else:
            values = _levels(100.0, m)
        series[f] = [PricePoint(day=d, value=v) for d, v in zip(days, values, strict=True)]
    asset_returns = 1.2 * moves[Factor.EQ_GLOBAL] + 0.5 * moves[Factor.EQ_US_TECH]
    return series, asset_returns, moves


def _closes(returns: np.ndarray) -> dict[str, Decimal]:
    return {d.isoformat(): v for d, v in zip(_days(), _levels(50.0, returns), strict=True)}


def _seed_assets(*asset_ids: str) -> None:
    with session_scope() as session:
        for asset_id in asset_ids:
            session.add(
                Asset(
                    id=asset_id,
                    isin=None,
                    ticker=None,
                    name=asset_id,
                    asset_type="etf",
                    asset_class="equity",
                    currency="EUR",
                    ter=None,
                    transferable=False,
                    price_kind="close",
                    price_source="yahoo:X",
                )
            )


@pytest.fixture
def market(db: None) -> Iterator[np.ndarray]:
    clock.set_now(NOW)
    series, returns, _ = _market()
    previous = prices_service.set_factor_source(_Factors(series))
    _seed_assets(ETF, STOCK, FUND, DEPOSIT)
    try:
        yield returns
    finally:
        prices_service.set_factor_source(previous)
        clock.reset()


def test_recompute_writes_betas_with_computed_at(market: np.ndarray) -> None:
    provider = FakePriceProvider(closes={ETF: _closes(market)})
    with use_price_provider(provider):
        run = impact_service.recompute_betas([ETF])

    betas = repository.get_betas([ETF])
    assert run.estimated == [ETF]
    assert {b.factor for b in betas} == set(Factor)
    by_factor = {b.factor: b for b in betas}
    assert abs(by_factor[Factor.EQ_GLOBAL].beta - Decimal("1.2")) < Decimal("0.001")
    assert abs(by_factor[Factor.EQ_US_TECH].beta - Decimal("0.5")) < Decimal("0.001")
    assert all(b.computed_at == NOW for b in betas)
    assert repository.last_computed_at() == NOW


def test_recompute_only_touches_the_requested_assets(market: np.ndarray) -> None:
    provider = FakePriceProvider(closes={ETF: _closes(market), STOCK: _closes(market * 2)})
    with use_price_provider(provider):
        impact_service.recompute_betas([ETF, STOCK])
        clock.set_now(NOW + timedelta(days=1))
        impact_service.recompute_betas([STOCK])

    etf = repository.get_betas([ETF])
    stock = repository.get_betas([STOCK])
    assert {b.computed_at for b in etf} == {NOW}
    assert {b.computed_at for b in stock} == {NOW + timedelta(days=1)}


def test_asset_without_enough_data_loses_old_betas_and_is_reported(market: np.ndarray) -> None:
    full = FakePriceProvider(closes={ETF: _closes(market)})
    with use_price_provider(full):
        impact_service.recompute_betas([ETF])
    short = {d: v for d, v in list(_closes(market).items())[:20]}
    with use_price_provider(FakePriceProvider(closes={ETF: short})):
        run = impact_service.recompute_betas([ETF])

    assert run.estimated == []
    assert ETF in run.missing
    assert repository.get_betas([ETF]) == []  # «sin betas» (D-050), no las antiguas


def test_a_missing_factor_keeps_the_stored_betas(market: np.ndarray) -> None:
    """Si un factor no tiene cierres (p. ej. el BCE no responde), no se borra nada."""
    with use_price_provider(FakePriceProvider(closes={ETF: _closes(market)})):
        impact_service.recompute_betas([ETF])
        before = repository.get_betas([ETF])
        series, _, _ = _market()
        series[Factor.RATES_EUR] = []
        prices_service.set_factor_source(_Factors(series))
        clock.set_now(NOW + timedelta(days=7))
        run = impact_service.recompute_betas()

    assert run.estimated == []
    assert "RATES_EUR" in run.missing[ETF]
    assert repository.get_betas([ETF]) == before
    assert repository.last_computed_at() == NOW  # la semana siguiente vuelve a intentarlo


def test_an_asset_without_prices_now_keeps_its_betas(market: np.ndarray) -> None:
    """Sin precios ahora (el proveedor no responde), el activo conserva sus betas."""
    with use_price_provider(FakePriceProvider(closes={ETF: _closes(market)})):
        impact_service.recompute_betas([ETF])
    before = repository.get_betas([ETF])
    with use_price_provider(FakePriceProvider()):
        run = impact_service.recompute_betas([ETF])

    assert ETF in run.missing
    assert repository.get_betas([ETF]) == before


def test_fixed_price_assets_are_skipped(market: np.ndarray) -> None:
    with use_price_provider(FakePriceProvider()):
        run = impact_service.recompute_betas([DEPOSIT])

    assert run.estimated == []
    assert run.missing == {}
    assert repository.get_betas([DEPOSIT]) == []


def test_all_catalog_assets_by_default(market: np.ndarray) -> None:
    provider = FakePriceProvider(closes={ETF: _closes(market), FUND: _closes(market * 0.8)})
    with use_price_provider(provider):
        run = impact_service.recompute_betas()

    assert sorted(run.estimated) == sorted([ETF, FUND])
    assert STOCK in run.missing  # en el catálogo, pero sin precios en este proveedor
    assert DEPOSIT not in run.missing  # precio fijo: no hay nada que estimar


def test_uses_adjusted_closes_when_the_provider_has_them(market: np.ndarray) -> None:
    flat = {d.isoformat(): Decimal("50") for d in _days()}  # cierre sin variación: no estimable
    adjusted = [PricePoint(day=date.fromisoformat(d), value=v) for d, v in _closes(market).items()]
    provider = _AdjustedProvider({ETF: adjusted}, closes={ETF: flat})
    with use_price_provider(provider):
        run = impact_service.recompute_betas([ETF])

    assert run.estimated == [ETF]


def test_window_ends_at_the_clock(market: np.ndarray) -> None:
    """Sin mirar al futuro: con el reloj atrás, la ventana termina en el reloj."""
    clock.set_now(datetime.combine(START + timedelta(days=200), datetime.min.time(), tzinfo=UTC))
    with use_price_provider(FakePriceProvider(closes={ETF: _closes(market)})):
        impact_service.recompute_betas([ETF])

    betas = repository.get_betas([ETF])
    assert {b.window_end for b in betas} == {START + timedelta(days=200)}


def test_weekly_recompute_only_when_due(market: np.ndarray) -> None:
    provider = FakePriceProvider(closes={ETF: _closes(market)})
    with use_price_provider(provider):
        assert impact_service.betas_due() is True  # nunca calculadas
        first = impact_service.recompute_betas_if_due()
        assert first is not None

        clock.set_now(NOW + timedelta(days=6))
        assert impact_service.betas_due() is False
        assert impact_service.recompute_betas_if_due() is None

        clock.set_now(NOW + timedelta(days=7))
        assert impact_service.betas_due() is True
        assert impact_service.recompute_betas_if_due() is not None
    assert repository.last_computed_at() == NOW + timedelta(days=7)
