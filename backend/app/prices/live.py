"""Proveedor en directo (`MARKET_DATA_PROVIDER=yahoo`, T2-24, D-065).

Refresco bajo demanda con caducidad, sin proceso en segundo plano:

- Acciones, ETF y EUR/USD: se vuelve a pedir el precio si el guardado tiene 60 s o más.
- Fondos (`nav_daily`): como mucho cada 6 h; solo publican un VL al día.
- Con el mercado cerrado no se vuelve a pedir hasta la apertura (o, si no se sabe, en 1 h).
- La primera vez se piden 3 años de cierres; después, los últimos 5 días.

Todo lo recibido se guarda en `price`/`fx_rate` con el instante del proveedor. Si el proveedor
falla, se sirve lo guardado y el último punto lleva `stale=True`; sin nada guardado, serie vacía
(y `service` responde `PRICE_UNAVAILABLE`). Nunca se rellena con el CSV ni se inventa un valor.
"""

import logging
import threading
from collections.abc import Callable, Sequence
from datetime import UTC, datetime, time, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Protocol

from app.core import clock
from app.prices import repository
from app.prices.catalog import load_catalog
from app.prices.provider import PricePoint
from app.prices.yahoo import Chart, ProviderError, YahooClient
from app.schemas.common import PriceKind

log = logging.getLogger(__name__)

PRICE_TTL = timedelta(seconds=60)
NAV_TTL = timedelta(hours=6)
CLOSED_RETRY = timedelta(hours=1)
FULL_RANGE = "3y"
SHORT_RANGE = "5d"
SOURCE = "yahoo"
ASSET_STEP = Decimal("0.0001")
FX_STEP = Decimal("0.000001")
LIVE_FX = {"EURUSD": "EURUSD=X"}
"""Pares en directo. El inverso (`USDEUR`) lo calcula `service.fx_quote`."""


class ChartSource(Protocol):
    def chart(self, symbol: str, range_: str) -> Chart: ...


def _rows(chart: Chart, step: Decimal) -> list[repository.Row]:
    """Las barras diarias de Yahoo traen ruido de coma flotante (`128.52000427`): se redondean
    como en `scripts/fetch_prices.py` para que coincidan con los CSV de `data/prices`."""
    rows = [
        (datetime.combine(day, time(), tzinfo=UTC), value.quantize(step, ROUND_HALF_EVEN))
        for day, value in chart.closes
    ]
    if chart.last_at is not None and chart.last_price is not None:
        rows.append((chart.last_at, chart.last_price.quantize(step, ROUND_HALF_EVEN)))
    return rows


def _points(rows: Sequence[repository.Row], stale: bool) -> list[PricePoint]:
    """Un punto por día: el de `ts` más reciente (el precio en directo gana al cierre del día)."""
    by_day: dict[datetime, repository.Row] = {}
    for ts, value in sorted(rows):
        by_day[datetime.combine(ts.date(), time(), tzinfo=UTC)] = (ts, value)
    points = [
        PricePoint(day=ts.date(), value=value, at=None if ts == midnight else ts)
        for midnight, (ts, value) in sorted(by_day.items())
    ]
    if stale and points:
        last = points[-1]
        points[-1] = PricePoint(day=last.day, value=last.value, at=last.at, stale=True)
    return points


def _next_refresh(chart: Chart, now: datetime, ttl: timedelta) -> datetime:
    if ttl >= NAV_TTL or chart.market_open:
        return now + ttl
    if chart.next_open is not None and chart.next_open > now:
        return max(now + ttl, chart.next_open)
    return now + max(ttl, CLOSED_RETRY)


class LiveProvider:
    def __init__(self, source: ChartSource | None = None) -> None:
        self._source: ChartSource = source or YahooClient()
        self._lock = threading.Lock()
        self._next: dict[str, datetime] = {}
        self._rows: dict[str, list[repository.Row]] = {}
        self._failed: set[str] = set()

    def closes(self, asset_id: str) -> list[PricePoint]:
        spec = load_catalog().get(asset_id)
        if spec is None or spec.symbol is None:
            return []
        ttl = NAV_TTL if spec.price_kind is PriceKind.NAV_DAILY else PRICE_TTL

        def save(rows: list[repository.Row]) -> None:
            repository.save_prices(asset_id, spec.currency, rows, SOURCE)

        return self._series(
            f"asset:{asset_id}",
            spec.symbol,
            ttl,
            ASSET_STEP,
            lambda: repository.load_prices(asset_id),
            save,
        )

    def fx_closes(self, pair: str) -> list[PricePoint]:
        symbol = LIVE_FX.get(pair)
        if symbol is None:
            return []

        def save(rows: list[repository.Row]) -> None:
            repository.save_fx(pair, rows, SOURCE)

        return self._series(
            f"fx:{pair}", symbol, PRICE_TTL, FX_STEP, lambda: repository.load_fx(pair), save
        )

    def _series(
        self,
        key: str,
        symbol: str,
        ttl: timedelta,
        step: Decimal,
        load: Callable[[], list[repository.Row]],
        save: Callable[[list[repository.Row]], None],
    ) -> list[PricePoint]:
        with self._lock:
            if key not in self._rows:
                self._rows[key] = load()
            now = clock.now()
            due = self._next.get(key)
            if due is None or now >= due:
                self._refresh(key, symbol, ttl, step, now, load, save)
            return _points(self._rows[key], stale=key in self._failed)

    def _refresh(
        self,
        key: str,
        symbol: str,
        ttl: timedelta,
        step: Decimal,
        now: datetime,
        load: Callable[[], list[repository.Row]],
        save: Callable[[list[repository.Row]], None],
    ) -> None:
        range_ = SHORT_RANGE if self._rows[key] else FULL_RANGE
        try:
            chart = self._source.chart(symbol, range_)
        except ProviderError as error:
            log.warning("Precio en directo no disponible (%s): %s", symbol, error)
            self._failed.add(key)
            self._next[key] = now + ttl
            return
        save(_rows(chart, step))
        self._rows[key] = load()
        self._failed.discard(key)
        self._next[key] = _next_refresh(chart, now, ttl)
