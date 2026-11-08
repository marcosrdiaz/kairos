"""`impact/betas.py`: OLS multivariante de rentabilidades diarias sobre los factores (SPEC §8.1)."""

from datetime import date, timedelta
from decimal import Decimal

import numpy as np
import pytest

from app.impact.betas import (
    BetaEstimate,
    InsufficientData,
    align_returns,
    estimate_betas,
)
from app.schemas.common import Factor

START = date(2024, 1, 1)
N_DAYS = 400


def _dates(n: int) -> list[date]:
    return [START + timedelta(days=i) for i in range(n)]


def _levels_from_returns(start: float, returns: np.ndarray) -> list[float]:
    levels = [start]
    for r in returns:
        levels.append(levels[-1] * (1 + r))
    return levels


def _synthetic(
    true_betas: dict[Factor, float], noise: float = 0.0, seed: int = 7
) -> tuple[dict[date, Decimal], dict[Factor, dict[date, Decimal]]]:
    """Precios de un activo cuyas rentabilidades son exactamente Σ β·f + ruido."""
    rng = np.random.default_rng(seed)
    days = _dates(N_DAYS + 1)
    factor_moves = {f: rng.normal(0, 0.01, N_DAYS) for f in Factor}
    factor_moves[Factor.RATES_EUR] = rng.normal(0, 0.0005, N_DAYS)  # en fracción, no en %

    factors: dict[Factor, dict[date, Decimal]] = {}
    for f, moves in factor_moves.items():
        if f is Factor.RATES_EUR:
            levels = list(0.025 + np.concatenate([[0.0], np.cumsum(moves)]))
        else:
            levels = _levels_from_returns(100.0, moves)
        factors[f] = {d: Decimal(repr(float(v))) for d, v in zip(days, levels, strict=True)}

    asset_ret = sum(true_betas.get(f, 0.0) * factor_moves[f] for f in Factor)
    asset_ret = asset_ret + rng.normal(0, noise, N_DAYS) if noise else asset_ret
    asset_levels = _levels_from_returns(50.0, np.asarray(asset_ret))
    prices = {d: Decimal(repr(float(v))) for d, v in zip(days, asset_levels, strict=True)}
    return prices, factors


def _by_factor(estimates: list[BetaEstimate]) -> dict[Factor, BetaEstimate]:
    return {e.factor: e for e in estimates}


def test_recovers_known_betas_on_perfect_fit() -> None:
    true = {
        Factor.EQ_GLOBAL: 0.9,
        Factor.EQ_US_TECH: 0.3,
        Factor.RATES_EUR: -6.5,
        Factor.OIL: 0.05,
        Factor.EURUSD: -0.8,
    }
    prices, factors = _synthetic(true)

    got = _by_factor(estimate_betas("X", prices, factors))

    assert set(got) == set(Factor)
    for f, beta in true.items():
        assert float(got[f].beta) == pytest.approx(beta, abs=1e-6)
        assert got[f].r2 == Decimal("1.00000000")
        assert got[f].n_obs == N_DAYS


def test_noise_gives_positive_std_err_and_r2_below_one() -> None:
    prices, factors = _synthetic({Factor.EQ_GLOBAL: 1.0}, noise=0.005)

    got = _by_factor(estimate_betas("X", prices, factors))

    eq = got[Factor.EQ_GLOBAL]
    assert float(eq.beta) == pytest.approx(1.0, abs=0.1)
    assert eq.std_err > 0
    assert Decimal("0.5") < eq.r2 < Decimal("1")
    # el R² es del modelo: igual en todas las filas del activo
    assert {e.r2 for e in got.values()} == {eq.r2}


def test_output_is_decimal_with_eight_places_and_window() -> None:
    prices, factors = _synthetic({Factor.EQ_GLOBAL: 1.0}, noise=0.005)

    est = estimate_betas("ABC", prices, factors)

    for e in est:
        assert e.asset_id == "ABC"
        for value in (e.beta, e.std_err, e.r2):
            assert isinstance(value, Decimal)
            assert value.as_tuple().exponent == -8
        assert e.window_start == START
        assert e.window_end == START + timedelta(days=N_DAYS)


def test_rates_use_absolute_change_others_percent_change() -> None:
    days = _dates(3)

    def series(*values: str) -> dict[date, Decimal]:
        return {d: Decimal(v) for d, v in zip(days, values, strict=True)}

    prices = series("10", "11", "11")
    factors = {
        Factor.EQ_GLOBAL: series("100", "102", "51"),
        Factor.RATES_EUR: series("0.0250", "0.0240", "0.0245"),
    }

    aligned = align_returns(prices, factors)

    assert aligned.dates == [days[1], days[2]]
    assert aligned.asset == pytest.approx([0.1, 0.0])
    assert aligned.factors[Factor.EQ_GLOBAL] == pytest.approx([0.02, -0.5])
    assert aligned.factors[Factor.RATES_EUR] == pytest.approx([-0.0010, 0.0005])


def test_dates_are_inner_joined_before_computing_returns() -> None:
    # El factor no cotiza el día 1: la rentabilidad del día 2 abarca 0 → 2 en las dos series.
    days = _dates(3)
    prices = {days[0]: Decimal("10"), days[1]: Decimal("20"), days[2]: Decimal("12")}
    factors = {Factor.OIL: {days[0]: Decimal("50"), days[2]: Decimal("55")}}

    aligned = align_returns(prices, factors)

    assert aligned.dates == [days[2]]
    assert aligned.asset == pytest.approx([0.2])
    assert aligned.factors[Factor.OIL] == pytest.approx([0.1])


def test_window_start_trims_older_observations() -> None:
    prices, factors = _synthetic({Factor.EQ_GLOBAL: 1.0}, noise=0.005)
    cut = START + timedelta(days=100)

    est = estimate_betas("X", prices, factors, window_start=cut)

    assert est[0].window_start == cut
    assert est[0].n_obs == N_DAYS - 100


def test_too_few_observations_raises() -> None:
    prices, factors = _synthetic({Factor.EQ_GLOBAL: 1.0})
    few = {d: v for d, v in prices.items() if d < START + timedelta(days=20)}

    with pytest.raises(InsufficientData):
        estimate_betas("X", few, factors)


def test_constant_price_raises_instead_of_inventing_betas() -> None:
    _, factors = _synthetic({Factor.EQ_GLOBAL: 1.0})
    flat = {d: Decimal("10") for d in _dates(N_DAYS + 1)}

    with pytest.raises(InsufficientData):
        estimate_betas("DEP-12M", flat, factors)


def test_zero_price_raises_instead_of_dividing_by_zero() -> None:
    prices, factors = _synthetic({Factor.EQ_GLOBAL: 1.0}, noise=0.005)
    prices[START + timedelta(days=10)] = Decimal("0")

    with pytest.raises(InsufficientData):
        estimate_betas("X", prices, factors)


def test_no_factors_raises() -> None:
    prices, _ = _synthetic({Factor.EQ_GLOBAL: 1.0})

    with pytest.raises(InsufficientData):
        estimate_betas("X", prices, {})


def test_window_end_trims_newer_observations() -> None:
    prices, factors = _synthetic({Factor.EQ_GLOBAL: 1.0}, noise=0.005)
    cut = START + timedelta(days=300)

    est = estimate_betas("X", prices, factors, window_end=cut)

    assert est[0].window_start == START
    assert est[0].window_end == cut
    assert est[0].n_obs == 300
