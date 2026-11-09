"""Variación de valor de una cartera entre dos instantes (`ValueChangeOut`). Funciones puras.

Reglas (D-057):

- Participaciones en `t` = Σ de las operaciones del libro con `ts ≤ t` (entran `initial`, `buy`,
  `dca_buy` y `transfer_in`; salen `sell` y `transfer_out`).
- Flujos del periodo = operaciones con `start < ts ≤ end`: `+amount_eur` las que entran y
  `−amount_eur` las que salen. Un traspaso deja un flujo negativo en el origen y uno positivo en
  el destino; en la cartera se compensan.
- Valor de un activo en `t` = participaciones × (último cierre no posterior a `t` × fx en `t`),
  a céntimos. Los totales son la suma de los activos.
- Sin ajustes de demo (los añade T2-02).
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Decimal

from app.schemas.portfolio import AssetValueChange

CENT = Decimal("0.01")
ZERO = Decimal(0)
INFLOWS = frozenset({"initial", "buy", "dca_buy", "transfer_in"})
OUTFLOWS = frozenset({"sell", "transfer_out"})

FORMULA = (
    "V_i(t) = units_i(t) × price_i(≤t) × fx_i(t) (a céntimos); units_i(t) = Σ operaciones con "
    "ts ≤ t; flows_i = Σ ±amount_eur con start < ts ≤ end; "
    "start_value = Σ V_i(start); end_value = Σ V_i(end); net_flows = Σ flows_i"
)


@dataclass(frozen=True)
class TxIn:
    asset_id: str
    ts: datetime
    type: str
    units: Decimal
    amount_eur: Decimal


@dataclass(frozen=True)
class Totals:
    start_value_eur: Decimal
    end_value_eur: Decimal
    net_flows_eur: Decimal
    by_asset: list[AssetValueChange]


def _sign(tx: TxIn) -> int:
    if tx.type in INFLOWS:
        return 1
    if tx.type in OUTFLOWS:
        return -1
    raise ValueError(f"Tipo de operación desconocido: {tx.type}")


def units_at(txs: Iterable[TxIn], at: datetime) -> dict[str, Decimal]:
    """Participaciones de cada activo en `at`. Omite los activos que quedan a cero."""
    units: dict[str, Decimal] = {}
    for tx in txs:
        if tx.ts <= at:
            units[tx.asset_id] = units.get(tx.asset_id, ZERO) + _sign(tx) * tx.units
    return {asset_id: u for asset_id, u in units.items() if u != 0}


def flows_between(txs: Iterable[TxIn], start: datetime, end: datetime) -> dict[str, Decimal]:
    """Dinero que entra (+) o sale (−) de cada activo en `(start, end]`."""
    flows: dict[str, Decimal] = {}
    for tx in txs:
        if start < tx.ts <= end:
            flows[tx.asset_id] = flows.get(tx.asset_id, ZERO) + _sign(tx) * tx.amount_eur
    return flows


def _value(units: Decimal | None, unit_eur: Decimal | None) -> Decimal:
    if not units:
        return ZERO.quantize(CENT)
    if unit_eur is None:
        raise ValueError("Falta el valor unitario de un activo con participaciones")
    return (units * unit_eur).quantize(CENT, rounding=ROUND_HALF_EVEN)


def summarize(
    start_units: Mapping[str, Decimal],
    end_units: Mapping[str, Decimal],
    flows: Mapping[str, Decimal],
    start_unit_eur: Mapping[str, Decimal],
    end_unit_eur: Mapping[str, Decimal],
) -> Totals:
    """Valor inicial, final y flujos por activo (por orden de `asset_id`) y sus totales."""
    by_asset = [
        AssetValueChange(
            asset_id=asset_id,
            start_value_eur=_value(start_units.get(asset_id), start_unit_eur.get(asset_id)),
            end_value_eur=_value(end_units.get(asset_id), end_unit_eur.get(asset_id)),
            flows_eur=flows.get(asset_id, ZERO).quantize(CENT, rounding=ROUND_HALF_EVEN),
        )
        for asset_id in sorted({*start_units, *end_units, *flows})
    ]
    return Totals(
        start_value_eur=sum((a.start_value_eur for a in by_asset), ZERO.quantize(CENT)),
        end_value_eur=sum((a.end_value_eur for a in by_asset), ZERO.quantize(CENT)),
        net_flows_eur=sum((a.flows_eur for a in by_asset), ZERO.quantize(CENT)),
        by_asset=by_asset,
    )
