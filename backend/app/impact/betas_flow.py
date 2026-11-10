"""Recalcular `factor_beta` desde las series de `prices` (T4-03).

Antes lo hacía `scripts/compute_betas.py` leyendo los CSV. Ahora es una función de `impact` que
pide las series a `prices.service`, así que sirve igual en modo demo (CSV de `data/prices` y
`data/factors`) y en directo (lo guardado en `price` y `factor_close`):

- Activo: `prices.service.beta_closes` (cierres ajustados por dividendos si el proveedor los da).
- Factores: `prices.service.factor_closes`, los cinco.
- Ventana: los últimos `years` años hasta el último día con cierre de los cinco factores, sin
  pasar del reloj (`clock`): nunca se mira al futuro.
- Se guarda con `computed_at`. Un activo que ya no se puede estimar pierde sus betas antiguas y
  sale como «sin betas» (D-050); los de precio fijo no tienen nada que estimar y se omiten.

Cuándo se ejecuta: `make betas` y el arranque (`compute_betas.py`), cada semana
(`recompute_betas_if_due`, desde `scripts/daily_update.py`) y al dar de alta un activo (T4-07).
"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from app.core import clock
from app.core.errors import AppError
from app.impact import repository
from app.impact.betas import BetaEstimate, InsufficientData, Series, estimate_betas
from app.prices import service as prices_service
from app.schemas.common import Factor

WINDOW_YEARS = 3
MAX_AGE = timedelta(days=7)
"""Las betas se recalculan si las últimas tienen una semana o más."""


@dataclass(frozen=True)
class BetaRun:
    """Resultado de un recálculo."""

    computed_at: datetime
    estimated: list[str] = field(default_factory=list)
    """Activos con betas nuevas."""
    missing: dict[str, str] = field(default_factory=dict)
    """Activos con precio de mercado que se quedan sin betas, con el motivo."""
    rows: int = 0
    window_start: date | None = None
    window_end: date | None = None
    estimates: list[BetaEstimate] = field(default_factory=list)


def _factor_series() -> dict[Factor, Series]:
    return {f: {p.day: p.value for p in prices_service.factor_closes(f)} for f in Factor}


def _has_market_prices(asset_id: str) -> bool | None:
    """`None` si `prices` no conoce el activo."""
    try:
        return prices_service.has_market_prices(asset_id)
    except AppError:
        return None


def recompute_betas(
    asset_ids: Iterable[str] | None = None, years: int = WINDOW_YEARS, save: bool = True
) -> BetaRun:
    """Recalcula y guarda las betas de `asset_ids` (por defecto, todo el catálogo de `prices`).

    Los activos tienen que estar en la tabla `asset` (FK de `factor_beta`). Con `save=False`
    solo calcula (`compute_betas.py --dry-run`).
    """
    ids = list(
        dict.fromkeys(prices_service.catalog_asset_ids() if asset_ids is None else asset_ids)
    )
    now = clock.now()
    factors = _factor_series()
    empty = [f.value for f, s in factors.items() if not s]
    if empty:
        # Fallo del proveedor (p. ej. el BCE no responde): no se toca nada de lo guardado.
        reason = f"sin cierres de los factores {', '.join(empty)}"
        missing = {a: reason for a in ids if _has_market_prices(a)}
        return BetaRun(computed_at=now, missing=missing)

    window_end = min(max(s) for s in factors.values())
    window_start = window_end - timedelta(days=365 * years)
    estimates: list[BetaEstimate] = []
    estimated: list[str] = []
    missing = {}
    # Se borran las betas antiguas de los de precio fijo y de los que, con datos, no se pueden
    # estimar. Uno sin precios ahora (el proveedor no responde) conserva las suyas.
    clear: list[str] = []
    for asset_id in ids:
        market = _has_market_prices(asset_id)
        if market is None:
            missing[asset_id] = f"{asset_id}: activo desconocido"
            continue
        if not market:
            clear.append(asset_id)
            continue
        prices = {p.day: p.value for p in prices_service.beta_closes(asset_id)}
        if not prices:
            missing[asset_id] = f"{asset_id}: sin precios (se conservan las betas anteriores)"
            continue
        try:
            estimates += estimate_betas(asset_id, prices, factors, window_start, window_end)
        except InsufficientData as exc:
            missing[asset_id] = str(exc)
            clear.append(asset_id)
            continue
        estimated.append(asset_id)

    rows = repository.replace_betas(estimates, clear=clear, computed_at=now) if save else 0
    return BetaRun(now, estimated, missing, rows, window_start, window_end, estimates)


def betas_due(max_age: timedelta = MAX_AGE) -> bool:
    """`True` si nunca se han calculado betas o las últimas tienen `max_age` o más."""
    last = repository.last_computed_at()
    return last is None or clock.now() - last >= max_age


def recompute_betas_if_due(max_age: timedelta = MAX_AGE) -> BetaRun | None:
    """Recalcula todo el catálogo si toca (actualización semanal). `None` si no tocaba."""
    if not betas_due(max_age):
        return None
    return recompute_betas()
