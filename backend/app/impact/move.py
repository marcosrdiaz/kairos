"""Atribución de "¿Por qué ha bajado?" (`explain_move`, diseño del MVP §4.3). Funciones puras.

Reglas:

- Ventana: `[now − periodo, now]`, con `day` = 1 día, `week` = 7 y `month` = 30.
- Cambio de un activo = valor final − valor inicial − flujos del periodo + ajuste de demo
  (D-031, D-075). Las compras, ventas y DCA no cuentan como movimiento de mercado.
- `change_eur` = Σ cambios por activo; `change_pct` = `change_eur` / valor inicial, a 4 decimales
  (0 si no había valor inicial).
- `by_event` son estimaciones; `unexplained_eur = change_eur − Σ impact_eur` ("otros movimientos
  del mercado").
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal

from app.schemas.impact import MoveAssetChange, MoveEventImpact, MovePeriod

CENT = Decimal("0.01")
PCT_STEP = Decimal("0.0001")
ZERO = Decimal(0)
PERIOD_DAYS: dict[MovePeriod, int] = {"day": 1, "week": 7, "month": 30}

FORMULA = (
    "Δ_i = V_i(end) − V_i(start) − flows_i + adj_i; change = Σ Δ_i; "
    "change_pct = change / Σ V_i(start); unexplained = change − Σ impact_e"
)

__all__ = ["PERIOD_DAYS", "AssetIn", "MovePeriod", "MoveResult", "attribute", "window"]


@dataclass(frozen=True)
class AssetIn:
    asset_id: str
    name: str
    start_value_eur: Decimal
    end_value_eur: Decimal
    flows_eur: Decimal
    adjustment_eur: Decimal
    """Ajuste de demo de los eventos del periodo (0 fuera del modo demo)."""


@dataclass(frozen=True)
class MoveResult:
    change_eur: Decimal
    change_pct: Decimal
    by_asset: list[MoveAssetChange]
    unexplained_eur: Decimal


def window(period: MovePeriod, now: datetime) -> tuple[datetime, datetime]:
    return now - timedelta(days=PERIOD_DAYS[period]), now


def _cents(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_EVEN)


def attribute(assets: Sequence[AssetIn], events: Sequence[MoveEventImpact]) -> MoveResult:
    changes = [
        MoveAssetChange(
            asset_id=a.asset_id,
            name=a.name,
            change_eur=_cents(a.end_value_eur - a.start_value_eur - a.flows_eur + a.adjustment_eur),
        )
        for a in assets
    ]
    by_asset = sorted(
        (c for c in changes if c.change_eur != ZERO),
        key=lambda c: (-abs(c.change_eur), c.asset_id),
    )
    change = _cents(sum((c.change_eur for c in changes), ZERO))
    start = sum((a.start_value_eur for a in assets), ZERO)
    pct = (change / start if start else ZERO).quantize(PCT_STEP, rounding=ROUND_HALF_EVEN)
    explained = sum((e.impact_eur for e in events), ZERO)
    return MoveResult(change, pct, by_asset, _cents(change - explained))
