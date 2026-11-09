"""DCA (RF-07): calendario y reparto de una aportación. Funciones puras (sin BD ni red).

Reglas:

- `day` es el día del mes (1-28) si el plan es mensual y el día ISO de la semana (1 = lunes,
  7 = domingo) si es semanal. Las fechas de ejecución son el inicio del día en UTC.
- El reparto `Σ weight = 1` se valida exacto (es `Decimal`); cada peso > 0 y sin activos repetidos.
- Importe de cada línea = `amount_eur × weight`, a céntimos con HALF_EVEN. El céntimo que sobre
  o falte por redondeo va a la primera línea (más peso; si empatan, menor `asset_id`), para que
  la suma sea exactamente el importe del plan.
- Las participaciones salen de `lots.size_trade(..., amount_eur=...)`.
"""

from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal

from app.schemas.portfolio import Frequency

CENT = Decimal("0.01")
ONE = Decimal(1)
WEEK_DAYS = 7

FORMULA = (
    "amount_line = amount_eur × weight (a céntimos; el resto del redondeo a la primera línea); "
    "unit_eur = price × fx; units = amount_line / unit_eur; nuevo lote con coste unit_eur"
)

Allocation = tuple[str, Decimal]
"""`(asset_id, weight)`."""


class InvalidAllocation(ValueError):
    """El reparto no suma 1, repite un activo o tiene un peso no positivo."""


class InvalidDay(ValueError):
    """Día de ejecución fuera de rango para la frecuencia."""


def day_start(at: datetime) -> datetime:
    """Inicio del día (UTC) que contiene `at`."""
    d = at.astimezone(UTC).date()
    return datetime(d.year, d.month, d.day, tzinfo=UTC)


def check_day(frequency: Frequency, day: int) -> None:
    top = 28 if frequency is Frequency.MONTHLY else WEEK_DAYS
    if not 1 <= day <= top:
        raise InvalidDay(f"el día debe estar entre 1 y {top} para un plan {frequency.value}")


def check_allocations(allocations: Sequence[Allocation]) -> None:
    assets = [asset_id for asset_id, _ in allocations]
    if len(set(assets)) != len(assets):
        raise InvalidAllocation("hay activos repetidos en el reparto")
    if any(weight <= 0 for _, weight in allocations):
        raise InvalidAllocation("cada peso del reparto tiene que ser mayor que cero")
    total = sum((weight for _, weight in allocations), Decimal(0))
    if total != ONE:
        raise InvalidAllocation(
            f"los pesos del reparto suman {total.normalize():f} y deben sumar 1"
        )


def ordered(allocations: Sequence[Allocation]) -> list[Allocation]:
    """Más peso primero; si empatan, por `asset_id`."""
    return sorted(allocations, key=lambda a: (-a[1], a[0]))


def split_amount(amount_eur: Decimal, allocations: Sequence[Allocation]) -> list[Allocation]:
    """Importe de cada línea, `(asset_id, amount_eur)`, en el orden de `ordered`."""
    lines = [
        (asset_id, (amount_eur * weight).quantize(CENT, rounding=ROUND_HALF_EVEN))
        for asset_id, weight in ordered(allocations)
    ]
    if not lines:
        return []
    remainder = amount_eur.quantize(CENT, rounding=ROUND_HALF_EVEN) - sum(a for _, a in lines)
    first_id, first_amount = lines[0]
    return [(first_id, first_amount + remainder), *lines[1:]]


def next_execution(frequency: Frequency, day: int, after: datetime, *, inclusive: bool) -> datetime:
    """Primera fecha de ejecución desde `after` (el propio día cuenta si `inclusive`)."""
    start = day_start(after).date()
    if frequency is Frequency.WEEKLY:
        ahead = (day - start.isoweekday()) % WEEK_DAYS
        if ahead == 0 and not inclusive:
            ahead = WEEK_DAYS
        found = start + timedelta(days=ahead)
    else:
        found = _monthly(start, day, inclusive)
    return datetime(found.year, found.month, found.day, tzinfo=UTC)


def _monthly(start: date, day: int, inclusive: bool) -> date:
    candidate = date(start.year, start.month, day)
    if candidate > start or (inclusive and candidate == start):
        return candidate
    year, month = (start.year + 1, 1) if start.month == 12 else (start.year, start.month + 1)
    return date(year, month, day)
