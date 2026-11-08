"""Betas de factor por OLS multivariante (SPEC §8.1). Funciones puras: series → estimaciones.

- Rentabilidad diaria del activo (en su divisa local) sobre los cinco factores **a la vez**, con
  término independiente. Al ser una regresión conjunta, el motor puede sumar `Σ β·s` sin contar dos
  veces lo que comparten factores correlacionados (`EQ_GLOBAL` y `EQ_US_TECH`).
- Las fechas se cruzan (inner join) **antes** de calcular rentabilidades: si un mercado cierra un
  día, la rentabilidad siguiente abarca el mismo intervalo en todas las series.
- `RATES_EUR` está en fracción (`0.0264` = 2,64 %): su "rentabilidad" es la variación absoluta,
  la misma unidad que el shock del evento. El resto, variación porcentual.
- El R² es el del modelo, igual en todas las filas de un activo.

numpy solo aquí dentro; la salida es `Decimal` con 8 decimales (`NUMERIC(20,8)`).
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal
from itertools import pairwise

import numpy as np
import numpy.typing as npt

from app.schemas.common import Factor

ABSOLUTE_CHANGE_FACTORS = frozenset({Factor.RATES_EUR})
MIN_OBSERVATIONS = 60
_PLACES = Decimal("0.00000001")

Series = Mapping[date, Decimal]


class InsufficientData(ValueError):
    """No hay datos suficientes (o con variación) para estimar betas con sentido."""


@dataclass(frozen=True)
class BetaEstimate:
    asset_id: str
    factor: Factor
    beta: Decimal
    std_err: Decimal
    r2: Decimal
    n_obs: int
    window_start: date
    window_end: date


@dataclass(frozen=True)
class AlignedReturns:
    """Rentabilidades en las fechas comunes; `dates[k]` es el final del intervalo k."""

    dates: list[date]
    asset: list[float]
    factors: dict[Factor, list[float]]


def _changes(levels: list[float], absolute: bool) -> list[float]:
    pairs = list(pairwise(levels))
    if absolute:
        return [b - a for a, b in pairs]
    return [b / a - 1 for a, b in pairs]


def align_returns(
    prices: Series,
    factors: Mapping[Factor, Series],
    window_start: date | None = None,
    window_end: date | None = None,
) -> AlignedReturns:
    """Cruza fechas y convierte niveles en rentabilidades (o variaciones absolutas en tipos)."""
    common = set(prices)
    for series in factors.values():
        common &= set(series)
    days = sorted(
        d
        for d in common
        if (window_start is None or d >= window_start) and (window_end is None or d <= window_end)
    )
    if len(days) < 2:
        return AlignedReturns(dates=[], asset=[], factors={f: [] for f in factors})

    asset = _changes([float(prices[d]) for d in days], absolute=False)
    factor_returns = {
        f: _changes([float(s[d]) for d in days], absolute=f in ABSOLUTE_CHANGE_FACTORS)
        for f, s in factors.items()
    }
    return AlignedReturns(dates=days[1:], asset=asset, factors=factor_returns)


def _to_decimal(value: float) -> Decimal:
    return Decimal(repr(value)).quantize(_PLACES, rounding=ROUND_HALF_EVEN)


def _ols(
    y: npt.NDArray[np.float64], x: npt.NDArray[np.float64]
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], float]:
    """Coeficientes, errores estándar (sin el término independiente) y R²."""
    n, k = x.shape
    design = np.column_stack([np.ones(n), x])
    xtx = design.T @ design
    if np.linalg.matrix_rank(xtx) < k + 1:
        raise InsufficientData("factores colineales o sin variación")
    coef = np.linalg.solve(xtx, design.T @ y)
    resid = y - design @ coef
    ssr = float(resid @ resid)
    sst = float(((y - y.mean()) ** 2).sum())
    if sst == 0.0:
        raise InsufficientData("el activo no varía: no hay sensibilidad que estimar")
    sigma2 = ssr / (n - k - 1)
    cov = sigma2 * np.linalg.inv(xtx)
    std_err = np.sqrt(np.clip(np.diag(cov), 0.0, None))
    r2 = min(max(1.0 - ssr / sst, 0.0), 1.0)
    return coef[1:], std_err[1:], r2


def estimate_betas(
    asset_id: str,
    prices: Series,
    factors: Mapping[Factor, Series],
    window_start: date | None = None,
    window_end: date | None = None,
) -> list[BetaEstimate]:
    """Una estimación por factor de `factors`. Lanza `InsufficientData` si no se puede estimar."""
    order = list(factors)
    aligned = align_returns(prices, factors, window_start, window_end)
    n = len(aligned.dates)
    if n < max(MIN_OBSERVATIONS, len(order) + 2):
        raise InsufficientData(f"{asset_id}: {n} observaciones (mínimo {MIN_OBSERVATIONS})")

    y = np.asarray(aligned.asset, dtype=np.float64)
    x = np.column_stack([np.asarray(aligned.factors[f], dtype=np.float64) for f in order])
    coef, std_err, r2 = _ols(y, x)

    common = sorted(set(prices).intersection(*(set(s) for s in factors.values())))
    first = next(d for d in common if window_start is None or d >= window_start)
    return [
        BetaEstimate(
            asset_id=asset_id,
            factor=f,
            beta=_to_decimal(float(coef[i])),
            std_err=_to_decimal(float(std_err[i])),
            r2=_to_decimal(r2),
            n_obs=n,
            window_start=first,
            window_end=aligned.dates[-1],
        )
        for i, f in enumerate(order)
    ]
