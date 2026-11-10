"""Impacto de una noticia (T4-30): funciones puras, sin BD ni red.

El clasificador (T4-29) solo dice **por dónde** llega la noticia (factores y empresas) y en qué
**dirección**. Todo lo que es un número sale de aquí, con datos de mercado:

- **Medido** (`measured`): la sesión que recoge la noticia ya ha cerrado. El shock de cada canal
  es su movimiento real esa sesión (cierre frente al anterior). Incluye todo lo que movió el
  mercado ese día, no solo esta noticia.
- **Estimado** (`volatility`): la sesión aún no ha cerrado. El tamaño del shock sale de cómo se
  movió ese factor o esa empresa en los **días de noticia fuerte** de los últimos tres años (días
  con un movimiento de al menos una desviación típica): percentiles 25, 50 y 75 del movimiento
  acumulado a `HORIZON_SESSIONS` sesiones desde ese día. La dirección es la de la clasificación;
  si es incierta, el rango es simétrico alrededor de cero.
"""

import statistics
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal

from app.schemas.common import AssetType, PriceKind
from app.schemas.news import EffectTiming, NewsDirection

Series = Sequence[tuple[date, Decimal]]
"""Cierres `(sesión, valor)` en orden de fecha."""

HORIZON_SESSIONS = 5
LOOKBACK = timedelta(days=3 * 365)
MIN_EVENTS = 20
US_CLOSE_UTC_HOUR = 21
_STEP = Decimal("0.00001")
_ZERO = Decimal("0")


@dataclass(frozen=True)
class Band:
    """Tamaño (sin signo) del movimiento a `horizon` sesiones en días de noticia fuerte."""

    p25: Decimal
    p50: Decimal
    p75: Decimal
    n: int
    horizon: int


def _q(value: Decimal) -> Decimal:
    return value.quantize(_STEP, rounding=ROUND_HALF_EVEN)


def _change(start: Decimal, end: Decimal, absolute: bool) -> Decimal:
    return end - start if absolute else end / start - 1


def _percentile(sorted_values: Sequence[Decimal], fraction: Decimal) -> Decimal:
    """Rango más cercano: sin interpolar, siempre un valor observado."""
    index = int((fraction * (len(sorted_values) - 1)).to_integral_value(ROUND_HALF_EVEN))
    return sorted_values[index]


def move_band(
    series: Series,
    as_of: date,
    horizon: int = HORIZON_SESSIONS,
    absolute: bool = False,
    min_events: int = MIN_EVENTS,
) -> Band | None:
    """Banda del movimiento en días de noticia fuerte antes de `as_of`, o `None` si hay menos
    de `MIN_EVENTS` días así (o la serie es demasiado corta)."""
    points = [(d, v) for d, v in series if as_of - LOOKBACK <= d < as_of and v != _ZERO]
    if len(points) < horizon + 2:
        return None
    daily = [_change(points[i - 1][1], points[i][1], absolute) for i in range(1, len(points))]
    sigma = Decimal(str(statistics.pstdev([float(x) for x in daily])))
    if sigma == _ZERO:
        return None
    moves: list[Decimal] = []
    for i in range(1, len(points) - horizon + 1):
        if abs(daily[i - 1]) >= sigma:
            moves.append(abs(_change(points[i - 1][1], points[i + horizon - 1][1], absolute)))
    if len(moves) < min_events:
        return None
    moves.sort()
    return Band(
        p25=_q(_percentile(moves, Decimal("0.25"))),
        p50=_q(_percentile(moves, Decimal("0.5"))),
        p75=_q(_percentile(moves, Decimal("0.75"))),
        n=len(moves),
        horizon=horizon,
    )


def signed_shocks(direction: NewsDirection, band: Band) -> tuple[Decimal, Decimal, Decimal]:
    """`(bajo, central, alto)` del shock de un canal según su dirección."""
    if direction is NewsDirection.UP:
        return band.p25, band.p50, band.p75
    if direction is NewsDirection.DOWN:
        return -band.p75, -band.p50, -band.p25
    return -band.p50, _ZERO, band.p50


def session_move(series: Series, day: date, absolute: bool = False) -> Decimal | None:
    """Movimiento de la sesión `day` frente a la anterior; `None` si no está esa sesión o no
    hay anterior."""
    for index, (session, value) in enumerate(series):
        if session == day:
            if index == 0 or series[index - 1][1] == _ZERO:
                return None
            return _q(_change(series[index - 1][1], value, absolute))
        if session > day:
            return None
    return None


def next_business_day(day: date) -> date:
    day += timedelta(days=1)
    while day.weekday() >= 5:
        day += timedelta(days=1)
    return day


def reaction_session(published_at: datetime) -> date:
    """Sesión que recoge la noticia: tras el cierre de EE. UU. o en fin de semana, la siguiente
    sesión hábil."""
    utc = published_at.astimezone(UTC)
    day = utc.date()
    if utc.hour >= US_CLOSE_UTC_HOUR:
        return next_business_day(day)
    return day if day.weekday() < 5 else next_business_day(day)


def effect_timing(
    price_kind: PriceKind, asset_type: AssetType, session: date
) -> tuple[EffectTiming, datetime | None]:
    """Cuándo se nota en una posición: en la sesión (acciones y ETF), con el siguiente valor
    liquidativo (fondos y planes) o nunca a diario (depósitos)."""
    if asset_type is AssetType.DEPOSIT:
        return EffectTiming.NO_DAILY_PRICE, None
    if price_kind is PriceKind.INTRADAY:
        day = session
        timing = EffectTiming.SAME_SESSION
    else:
        day = next_business_day(session)
        timing = EffectTiming.NEXT_NAV
    return timing, datetime(day.year, day.month, day.day, tzinfo=UTC)
