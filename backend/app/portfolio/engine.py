"""Valoración de una cartera: funciones puras (entrada → salida, sin BD ni red).

Reglas (`SPEC.md` §7, RF-03):

- `value_eur = units × price × fx`, redondeado a céntimos (HALF_EVEN) por posición.
- `total_eur = Σ value_eur` (así el total cuadra con la suma de lo que se muestra).
- `avg_cost_eur = Σ(units × coste) / units`; `unrealized_pnl_eur = value_eur − coste total`.
- `weight` y `allocation` = valor / total, a 4 decimales.
- `change_week_eur = total − valor de hace 7 días con las mismas participaciones`;
  `change_week_pct = cambio / valor de hace 7 días`, a 4 decimales.
- Ajuste de demo (D-031, solo `DEMO_MODE=true`): se suma al `value_eur` de su posición, así que
  entra en el total, el peso, la plusvalía y el cambio semanal. El valor de hace 7 días no lo lleva.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Decimal

from app.schemas.common import AssetClass, AssetType, PriceKind
from app.schemas.portfolio import AllocationOut, PositionOut

CENT = Decimal("0.01")
FRACTION_STEP = Decimal("0.0001")
UNIT_STEP = Decimal("0.00000001")
ZERO = Decimal(0)

FORMULA = (
    "value_eur_i = units_i × price_i × fx_i (a céntimos) + ajuste_demo_i; "
    "total_eur = Σ value_eur_i; "
    "weight_i = value_eur_i / total_eur; "
    "change_week = total_eur − Σ units_i × price_i,−7d × fx_i,−7d"
)


def _q(value: Decimal, step: Decimal) -> Decimal:
    return value.quantize(step, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class LotIn:
    asset_id: str
    acquired_at: datetime
    units: Decimal
    cost_eur_per_unit: Decimal


@dataclass(frozen=True)
class AssetIn:
    id: str
    isin: str | None
    ticker: str | None
    name: str
    asset_type: AssetType
    asset_class: AssetClass
    transferable: bool


@dataclass(frozen=True)
class QuoteIn:
    """Precio actual del activo y, si se conoce, su valor unitario en € de hace 7 días."""

    price: Decimal
    currency: str
    price_at: datetime
    price_kind: PriceKind
    fx_rate: Decimal
    """Divisa del precio → EUR (`1` si ya está en euros)."""
    week_ago_unit_eur: Decimal | None = None
    """`price × fx` de hace 7 días. `None` = sin dato: la posición no aporta cambio semanal."""


@dataclass(frozen=True)
class Valuation:
    total_eur: Decimal
    change_week_eur: Decimal
    change_week_pct: Decimal
    allocation: AllocationOut
    positions: list[PositionOut]


@dataclass(frozen=True)
class _Holding:
    asset_id: str
    units: Decimal
    cost_eur: Decimal
    first_acquired_at: datetime


def aggregate_lots(lots: Iterable[LotIn]) -> list[_Holding]:
    """Suma los lotes abiertos por activo. Ignora los lotes sin participaciones."""
    units: dict[str, Decimal] = {}
    cost: dict[str, Decimal] = {}
    first: dict[str, datetime] = {}
    for lot in lots:
        if lot.units <= 0:
            continue
        units[lot.asset_id] = units.get(lot.asset_id, ZERO) + lot.units
        cost[lot.asset_id] = cost.get(lot.asset_id, ZERO) + lot.units * lot.cost_eur_per_unit
        prev = first.get(lot.asset_id)
        first[lot.asset_id] = lot.acquired_at if prev is None else min(prev, lot.acquired_at)
    return [_Holding(a, units[a], cost[a], first[a]) for a in units]


def _fraction(part: Decimal, total: Decimal) -> Decimal:
    return _q(part / total, FRACTION_STEP) if total else _q(ZERO, FRACTION_STEP)


def value_portfolio(
    lots: Iterable[LotIn],
    assets: Mapping[str, AssetIn],
    quotes: Mapping[str, QuoteIn],
    adjustments: Mapping[str, Decimal] | None = None,
) -> Valuation:
    """Valora los lotes abiertos. `assets` y `quotes` deben tener todos los activos de `lots`.

    `adjustments`: ajuste de demo en € por activo. Los de activos sin posición se ignoran.
    """
    adjust = adjustments or {}
    holdings = aggregate_lots(lots)
    values: dict[str, Decimal] = {}
    week_total = ZERO
    for h in holdings:
        quote = quotes[h.asset_id]
        market_value = _q(h.units * quote.price * quote.fx_rate, CENT)
        values[h.asset_id] = market_value + adjust.get(h.asset_id, ZERO)
        week_unit = quote.week_ago_unit_eur
        week_total += market_value if week_unit is None else _q(h.units * week_unit, CENT)
    total = sum(values.values(), ZERO)

    positions: list[PositionOut] = []
    for h in holdings:
        asset, quote, value = assets[h.asset_id], quotes[h.asset_id], values[h.asset_id]
        positions.append(
            PositionOut(
                asset_id=asset.id,
                isin=asset.isin,
                ticker=asset.ticker,
                name=asset.name,
                asset_type=asset.asset_type,
                asset_class=asset.asset_class,
                units=_q(h.units, UNIT_STEP),
                avg_cost_eur=_q(h.cost_eur / h.units, CENT),
                price=quote.price,
                price_currency=quote.currency,
                price_at=quote.price_at,
                price_kind=quote.price_kind,
                fx_rate=quote.fx_rate,
                value_eur=value,
                weight=_fraction(value, total),
                unrealized_pnl_eur=value - _q(h.cost_eur, CENT),
                transferable=asset.transferable,
                first_acquired_at=h.first_acquired_at,
            )
        )
    positions.sort(key=lambda p: (-p.value_eur, p.asset_id))

    by_class = {c: ZERO for c in AssetClass}
    for p in positions:
        by_class[p.asset_class] += p.value_eur
    allocation = AllocationOut(
        equity=_fraction(by_class[AssetClass.EQUITY], total),
        fixed_income=_fraction(by_class[AssetClass.FIXED_INCOME], total),
        cash=_fraction(by_class[AssetClass.CASH], total),
        mixed=_fraction(by_class[AssetClass.MIXED], total),
    )
    change = total - week_total
    return Valuation(
        total_eur=total,
        change_week_eur=change,
        change_week_pct=_fraction(change, week_total),
        allocation=allocation,
        positions=positions,
    )
