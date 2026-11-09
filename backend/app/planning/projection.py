"""Motor de proyección con DCA (T1-14, diseño del MVP §4.3). Funciones puras, sin BD.

- Rentabilidad de cada escenario: media de `assumptions.json` ponderada por la asignación
  **objetivo**, a 5 decimales.
- Capitalización mensual con el tipo equivalente `(1 + r)^(1/12) − 1` (las rentabilidades de
  `assumptions.json` son geométricas anuales) y aportación al final de cada mes.
- Horizonte: los meses que quedan desde el mes actual hasta el 31 de diciembre del año de la meta.

Con el ejemplo del contrato (34.311,68 €, 300 €/mes, 169 meses, 5,740 %) da 152.181,69 €.
"""

from collections.abc import Iterable, Mapping
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Decimal, localcontext

from app.schemas.portfolio import Frequency, TargetAllocation

CENT = Decimal("0.01")
RATE_STEP = Decimal("0.00001")
ZERO = Decimal("0")
WEEKS_PER_YEAR = Decimal("52")
MONTHS_PER_YEAR = Decimal("12")

ReturnsByClass = Mapping[str, Decimal]
"""Rentabilidad anual por clase (`equity`, `fixed_income`, `cash`) de un escenario."""

DcaContribution = tuple[Decimal, Frequency, bool]
"""Importe, frecuencia y si el plan está activo."""


def months_until_goal(now: datetime, goal_year: int) -> int:
    """Meses completos desde el mes de `now` hasta diciembre de `goal_year`. Nunca negativo."""
    return max(0, (goal_year - now.year) * 12 + (12 - now.month))


def blended_return(target: TargetAllocation, returns: ReturnsByClass) -> Decimal:
    """Σ peso objetivo × rentabilidad de la clase, a 5 decimales (HALF_EVEN)."""
    total = (
        target.equity * returns["equity"]
        + target.fixed_income * returns["fixed_income"]
        + target.cash * returns["cash"]
    )
    return total.quantize(RATE_STEP, rounding=ROUND_HALF_EVEN)


def monthly_contribution(plans: Iterable[DcaContribution]) -> Decimal:
    """Aportación mensual equivalente de los planes activos (semanal × 52 / 12), a céntimos."""
    total = ZERO
    for amount, frequency, active in plans:
        if not active:
            continue
        if frequency == Frequency.WEEKLY:
            total += amount * WEEKS_PER_YEAR / MONTHS_PER_YEAR
        else:
            total += amount
    return total.quantize(CENT, rounding=ROUND_HALF_EVEN)


def future_value(
    current: Decimal, monthly: Decimal, annual_return: Decimal, months: int
) -> Decimal:
    """Valor al final del horizonte, a céntimos (HALF_EVEN). Sin redondeos intermedios."""
    with localcontext() as ctx:
        ctx.prec = 40
        rate = (1 + annual_return) ** (Decimal(1) / MONTHS_PER_YEAR) - 1
        value = current
        for _ in range(months):
            value = value * (1 + rate) + monthly
    return value.quantize(CENT, rounding=ROUND_HALF_EVEN)


def gap(goal: Decimal, base_value: Decimal) -> Decimal:
    """Lo que falta al escenario base para llegar a la meta; 0 si la alcanza."""
    return max(ZERO, goal - base_value).quantize(CENT, rounding=ROUND_HALF_EVEN)
