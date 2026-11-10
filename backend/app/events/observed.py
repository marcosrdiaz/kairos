"""Shock medido de un evento (D-025, D-089): lógica pura, sin BD ni red.

La variación de cada factor (y de cada empresa afectada) es el cierre de la sesión que recoge el
evento frente al cierre anterior: relativa en todos salvo `RATES_EUR`, que es una rentabilidad y
va en diferencia absoluta. La usan `events/service.py` (en producción, con los cierres de
`prices`) y `scripts/fetch_prices.py` (para el `observed` de los JSON del replay).

Si la sesión que recoge el evento aún no ha cerrado para **todos** los factores, el evento está
pendiente de cierre (`None`): no se usa un precio intradía como si fuera el cierre.
"""

from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal

from app.schemas.common import Factor
from app.schemas.events import EventObserved

US_CLOSE_UTC_HOUR = 21
"""Un evento a partir de esta hora UTC lo recoge la sesión del día siguiente."""
OBSERVED_STEP = Decimal("0.00001")
ABSOLUTE_FACTORS = frozenset({Factor.RATES_EUR})

Series = Sequence[tuple[date, Decimal]]
"""Cierres `(sesión, valor)` en orden de fecha."""


def reaction_date(occurred_at: datetime) -> date:
    """Sesión que recoge el evento: tras el cierre de EE. UU., la del día siguiente."""
    utc = occurred_at.astimezone(UTC)
    return utc.date() + timedelta(days=1) if utc.hour >= US_CLOSE_UTC_HOUR else utc.date()


def series_change(series: Series, day: date, absolute: bool = False) -> Decimal | None:
    """Variación de la primera sesión desde `day` frente a la anterior, o `None` si esa sesión
    aún no está o no tiene sesión anterior."""
    for index, (session, value) in enumerate(series):
        if session >= day:
            if index == 0:
                return None
            previous = series[index - 1][1]
            change = value - previous if absolute else value / previous - 1
            return change.quantize(OBSERVED_STEP, rounding=ROUND_HALF_EVEN)
    return None


def measure(
    day: date,
    factor_series: Mapping[Factor, Series],
    company_series: Mapping[str, Series],
) -> EventObserved | None:
    """`observed` de la sesión que empieza en `day` (ver `reaction_date`), con todos los factores.
    `None` si a algún factor o empresa le falta esa sesión: pendiente de cierre."""
    factors: dict[Factor, Decimal] = {}
    for factor in Factor:
        change = series_change(factor_series.get(factor, []), day, factor in ABSOLUTE_FACTORS)
        if change is None:
            return None
        factors[factor] = change
    companies: dict[str, Decimal] = {}
    for key, series in company_series.items():
        change = series_change(series, day)
        if change is None:
            return None
        companies[key] = change
    return EventObserved(factors=factors, companies=companies)
