"""Compra y venta sobre lotes fiscales: funciones puras (entrada → salida, sin BD ni red).

Reglas (`SPEC.md` §7, RF-04/RF-05):

- `unit_eur = price × fx`, a 8 decimales. Es el coste por participación de un lote comprado.
- Por participaciones: `amount_eur = units × price × fx`, a céntimos.
- Por importe: `units = amount_eur / unit_eur`, a 8 decimales; `amount_eur` es el pedido.
- La venta consume lotes por FIFO (`acquired_at`, en el orden recibido si empatan).
- `realized_gain_eur = amount_eur − Σ(units × coste del lote)`, a céntimos.
Todo con HALF_EVEN.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Decimal

CENT = Decimal("0.01")
UNIT_STEP = Decimal("0.00000001")
ZERO = Decimal(0)

FORMULA_BUY = (
    "unit_eur = price × fx; units = amount_eur / unit_eur (o amount_eur = units × price × fx); "
    "nuevo lote con coste unit_eur"
)
FORMULA_SELL = (
    "unit_eur = price × fx; amount_eur = units × price × fx (o units = amount_eur / unit_eur); "
    "lotes consumidos por FIFO; realized_gain_eur = amount_eur − Σ units_lote × coste_lote"
)


def _q(value: Decimal, step: Decimal) -> Decimal:
    return value.quantize(step, rounding=ROUND_HALF_EVEN)


class InsufficientUnits(ValueError):
    """Se piden más participaciones de las que hay en los lotes abiertos."""

    def __init__(self, requested: Decimal, available: Decimal) -> None:
        super().__init__(f"se piden {requested} participaciones y hay {available}")
        self.requested = requested
        self.available = available


@dataclass(frozen=True)
class OpenLot:
    lot_id: str
    acquired_at: datetime
    units: Decimal
    """Participaciones que quedan en el lote (`units_remaining`)."""
    cost_eur_per_unit: Decimal


@dataclass(frozen=True)
class Trade:
    units: Decimal
    amount_eur: Decimal
    unit_eur: Decimal


@dataclass(frozen=True)
class Outcome:
    """Efecto de una operación sobre los lotes de un activo."""

    consumed: list[OpenLot]
    """Parte de cada lote que se vende (`units` = participaciones consumidas de ese lote)."""
    created: list[OpenLot]
    """Lote nuevo de una compra (sin `lot_id` hasta guardarlo)."""
    realized_gain_eur: Decimal | None
    units_after: Decimal
    avg_cost_eur_after: Decimal


def size_trade(
    price: Decimal,
    fx_rate: Decimal,
    *,
    units: Decimal | None = None,
    amount_eur: Decimal | None = None,
) -> Trade:
    """Participaciones e importe de una operación pedida por uno de los dos (exactamente uno)."""
    if (units is None) == (amount_eur is None):
        raise ValueError("indica exactamente uno de units o amount_eur")
    unit_eur = _q(price * fx_rate, UNIT_STEP)
    if units is not None:
        return Trade(_q(units, UNIT_STEP), _q(units * price * fx_rate, CENT), unit_eur)
    assert amount_eur is not None
    return Trade(_q(amount_eur / unit_eur, UNIT_STEP), _q(amount_eur, CENT), unit_eur)


def fifo_order(lots: Sequence[OpenLot]) -> list[OpenLot]:
    """Lotes abiertos del más antiguo al más reciente (orden estable si empatan)."""
    return sorted((lot for lot in lots if lot.units > 0), key=lambda lot: lot.acquired_at)


def avg_cost(lots: Sequence[OpenLot]) -> tuple[Decimal, Decimal]:
    """Participaciones totales y coste medio por participación (a céntimos; 0 si no hay)."""
    units = sum((lot.units for lot in lots), ZERO)
    if not units:
        return ZERO, _q(ZERO, CENT)
    cost = sum((lot.units * lot.cost_eur_per_unit for lot in lots), ZERO)
    return units, _q(cost / units, CENT)


def buy(lots: Sequence[OpenLot], trade: Trade, at: datetime) -> Outcome:
    """Lote nuevo con `trade.units` a coste `trade.unit_eur`, adquirido en `at`."""
    new_lot = OpenLot("", at, trade.units, trade.unit_eur)
    units_after, avg_after = avg_cost([*fifo_order(lots), new_lot])
    return Outcome([], [new_lot], None, units_after, avg_after)


def sell_fifo(lots: Sequence[OpenLot], trade: Trade) -> Outcome:
    """Consume `trade.units` de los lotes por FIFO. Lanza `InsufficientUnits` si no llegan."""
    ordered = fifo_order(lots)
    available = sum((lot.units for lot in ordered), ZERO)
    if trade.units > available:
        raise InsufficientUnits(trade.units, available)
    pending = trade.units
    consumed: list[OpenLot] = []
    remaining: list[OpenLot] = []
    for lot in ordered:
        take = min(pending, lot.units)
        if take > 0:
            consumed.append(OpenLot(lot.lot_id, lot.acquired_at, take, lot.cost_eur_per_unit))
            pending -= take
        if lot.units > take:
            remaining.append(
                OpenLot(lot.lot_id, lot.acquired_at, lot.units - take, lot.cost_eur_per_unit)
            )
    cost = _q(sum((c.units * c.cost_eur_per_unit for c in consumed), ZERO), CENT)
    units_after, avg_after = avg_cost(remaining)
    return Outcome(consumed, [], trade.amount_eur - cost, units_after, avg_after)
