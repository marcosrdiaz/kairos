"""Plan de inversión: asignación actual y desviación (RF-22). Funciones puras.

Reglas (D-057):

- `current` reparte el valor de la cartera en renta variable, renta fija y liquidez, a 4
  decimales. `mixed` (el plan de pensiones de Javier) cuenta mitad renta variable y mitad renta
  fija, como en `assumptions.json` (D-038), porque el plan no tiene objetivo para `mixed`.
- `drift_equity = current.equity − target.equity`; `drift_exceeded = |drift_equity| > umbral`
  (igual al umbral no lo supera).
- Una cartera sin valor no tiene desviación: `current` a cero, `drift_equity = 0`.
- El objetivo suma exactamente 1 y el umbral está en (0, 1].
"""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

from app.schemas.common import AssetClass
from app.schemas.portfolio import TargetAllocation

FRACTION_STEP = Decimal("0.0001")
ZERO = Decimal(0)
ONE = Decimal(1)
HALF = Decimal("0.5")

FORMULA = (
    "current_c = (V_c + V_mixed/2 si c ∈ {equity, fixed_income}) / Σ V (a 4 decimales); "
    "drift_equity = current_equity − target_equity; drift_exceeded = |drift_equity| > umbral"
)


@dataclass(frozen=True)
class PlanCheck:
    drift_equity: Decimal
    drift_exceeded: bool


def _q(value: Decimal) -> Decimal:
    return value.quantize(FRACTION_STEP, rounding=ROUND_HALF_EVEN)


def current_allocation(values: Mapping[AssetClass, Decimal]) -> TargetAllocation:
    """Peso de cada clase en el valor total, con `mixed` repartido a medias."""
    total = sum(values.values(), ZERO)
    if total <= 0:
        return TargetAllocation(equity=ZERO, fixed_income=ZERO, cash=ZERO)
    half_mixed = values.get(AssetClass.MIXED, ZERO) * HALF
    equity = values.get(AssetClass.EQUITY, ZERO) + half_mixed
    fixed_income = values.get(AssetClass.FIXED_INCOME, ZERO) + half_mixed
    cash = values.get(AssetClass.CASH, ZERO)
    return TargetAllocation(
        equity=_q(equity / total), fixed_income=_q(fixed_income / total), cash=_q(cash / total)
    )


def assess(target: TargetAllocation, threshold: Decimal, current: TargetAllocation) -> PlanCheck:
    if current.equity == current.fixed_income == current.cash == ZERO:
        return PlanCheck(drift_equity=ZERO, drift_exceeded=False)
    drift = _q(current.equity - target.equity)
    return PlanCheck(drift_equity=drift, drift_exceeded=abs(drift) > threshold)


def target_error(target: TargetAllocation, threshold: Decimal) -> str | None:
    """Motivo por el que el objetivo o el umbral no valen, o `None` si valen."""
    parts = (target.equity, target.fixed_income, target.cash)
    if any(p < 0 for p in parts):
        return "Ningún peso del objetivo puede ser negativo."
    if sum(parts, ZERO) != ONE:
        return "Los pesos del objetivo deben sumar exactamente 1 (100 %)."
    if not ZERO < threshold <= ONE:
        return "El umbral de desviación debe estar entre 0 (sin incluir) y 1."
    return None
