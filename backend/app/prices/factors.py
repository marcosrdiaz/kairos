"""Series de los 5 factores (`Factor`): de dónde salen sus cierres diarios (T4-01).

- `OfflineFactors` (modo demo): `data/factors/<FACTOR>.csv` (`date,value`), los de T1-09.
- `LiveFactors` (`MARKET_DATA_PROVIDER=yahoo`): Yahoo para `EQ_GLOBAL`, `EQ_US_TECH`, `OIL` y
  `EURUSD`, y el BCE para `RATES_EUR`, con los mismos símbolos y decimales que
  `scripts/fetch_prices.py`. Lo recibido se guarda en `factor_close` con fecha y fuente.

Solo cierres de sesiones ya terminadas: nada de hoy ni de fin de semana (como `fetch_prices.py`).
Se refresca como mucho cada hora; la primera vez se piden 3 años y después los últimos días. Si
el proveedor falla, se sirve lo guardado y el último punto lleva `stale=True`; sin nada guardado,
serie vacía. Nunca se rellena con el CSV ni se inventa un valor.
"""

import csv
import logging
import threading
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from pathlib import Path
from typing import Protocol

from app.core import clock
from app.prices import ecb, repository
from app.prices.live import ChartSource
from app.prices.provider import DEFAULT_FACTORS_DIR, PricePoint
from app.prices.yahoo import ProviderError, YahooClient
from app.schemas.common import Factor, SourceKind, SourceRef

log = logging.getLogger(__name__)

YAHOO_FACTORS: dict[Factor, tuple[str, int]] = {
    Factor.EQ_GLOBAL: ("IWDA.AS", 4),  # MSCI World en EUR
    Factor.EQ_US_TECH: ("^NDX", 4),
    Factor.OIL: ("BZ=F", 4),
    Factor.EURUSD: ("EURUSD=X", 6),
}
"""Igual que `YAHOO_FACTORS` de `scripts/fetch_prices.py`: símbolo y decimales."""
FACTOR_TTL = timedelta(hours=1)
FULL_YEARS = 3
SHORT_RANGE = "5d"
SHORT_DAYS = timedelta(days=10)


class FactorSource(Protocol):
    def factor_closes(self, factor: Factor) -> list[PricePoint]:
        """Cierres del factor en orden ascendente de fecha. Vacío si no hay datos."""
        ...

    def source_of(self, factor: Factor, day: date) -> str | None:
        """Fuente del cierre de `day` (`yahoo:^NDX`, `ecb:…`, `csv:…`), para la traza."""
        ...


class RatesSource(Protocol):
    def rates(self, start: date) -> list[tuple[date, Decimal]]: ...


STALE = " (último cierre guardado: el proveedor no respondió)"


@dataclass(frozen=True)
class FactorCloseOut:
    factor: Factor
    day: date
    value: Decimal
    """`RATES_EUR` en fracción; `EURUSD`, dólares por euro; el resto, el nivel del índice."""
    stale: bool
    source: SourceRef


def last_close(
    source: FactorSource, factor: Factor, points: list[PricePoint]
) -> FactorCloseOut | None:
    """El último de `points` con su fecha y su fuente para la traza; `None` si no hay ninguno."""
    if not points:
        return None
    last = points[-1]
    raw = source.source_of(factor, last.day) or "desconocida"
    label = f"Cierre de {factor.value}: {source_label(raw)}" + (STALE if last.stale else "")
    as_of = datetime.combine(last.day, time(), tzinfo=UTC)
    ref = SourceRef(kind=SourceKind.PRICE, label=label, ref=factor.value, as_of=as_of)
    return FactorCloseOut(
        factor=factor, day=last.day, value=last.value, stale=last.stale, source=ref
    )


def source_label(source: str) -> str:
    """Texto de la fuente para la traza: `yahoo:^NDX` → «Yahoo Finance (^NDX)»."""
    if source.startswith("yahoo:"):
        return f"Yahoo Finance ({source.removeprefix('yahoo:')})"
    if source.startswith("ecb:"):
        return "BCE, curva AAA del área euro a 10 años"
    return source.removeprefix("csv:")


# --- Offline ---


class OfflineFactors:
    """Lee cada CSV una vez y lo guarda en memoria. A diferencia de los precios, admite valores
    negativos o cero (`RATES_EUR`)."""

    def __init__(self, factors_dir: Path = DEFAULT_FACTORS_DIR) -> None:
        self.factors_dir = factors_dir
        self._cache: dict[Factor, list[PricePoint]] = {}

    def factor_closes(self, factor: Factor) -> list[PricePoint]:
        if factor not in self._cache:
            self._cache[factor] = self._read(self.factors_dir / f"{factor.value}.csv")
        return list(self._cache[factor])

    def source_of(self, factor: Factor, day: date) -> str | None:
        return f"csv:data/factors/{factor.value}.csv"

    @staticmethod
    def _read(path: Path) -> list[PricePoint]:
        if not path.is_file():
            return []
        points: list[PricePoint] = []
        with path.open(encoding="utf-8", newline="") as fh:
            for n, row in enumerate(csv.DictReader(fh), start=2):
                raw_day, raw_value = (row.get("date") or "").strip(), (row.get("value") or "")
                if not raw_day and not raw_value.strip():
                    continue
                try:
                    value = Decimal(raw_value.strip())
                    if not value.is_finite():
                        raise InvalidOperation
                    points.append(PricePoint(day=date.fromisoformat(raw_day), value=value))
                except (ValueError, InvalidOperation) as exc:
                    raise ValueError(f"{path.name}, línea {n}: fila no válida {row!r}") from exc
        return sorted(points, key=lambda p: p.day)


# --- En directo ---


def _sessions(rows: list[tuple[date, Decimal]], today: date) -> list[tuple[date, Decimal]]:
    """Solo sesiones ya cerradas: ni la de hoy (puede estar abierta) ni fines de semana."""
    return [(day, value) for day, value in rows if day < today and day.weekday() < 5]


def _years_before(day: date, years: int) -> date:
    try:
        return day.replace(year=day.year - years)
    except ValueError:  # 29 de febrero
        return day.replace(year=day.year - years, day=28)


class LiveFactors:
    def __init__(self, charts: ChartSource | None = None, rates: RatesSource | None = None) -> None:
        self._charts: ChartSource = charts or YahooClient()
        self._rates: RatesSource = rates or ecb.EcbClient()
        self._lock = threading.Lock()
        self._next: dict[Factor, datetime] = {}
        self._rows: dict[Factor, list[repository.FactorRow]] = {}
        self._failed: set[Factor] = set()

    def factor_closes(self, factor: Factor) -> list[PricePoint]:
        with self._lock:
            if factor not in self._rows:
                self._rows[factor] = repository.load_factor(factor.value)
            now = clock.now()
            due = self._next.get(factor)
            if due is None or now >= due:
                self._refresh(factor, now)
            return self._points(factor)

    def _points(self, factor: Factor) -> list[PricePoint]:
        points = [PricePoint(day=day, value=value) for day, value, _ in self._rows[factor]]
        if factor in self._failed and points:
            last = points[-1]
            points[-1] = PricePoint(day=last.day, value=last.value, stale=True)
        return points

    def _refresh(self, factor: Factor, now: datetime) -> None:
        today = now.date()
        full = not self._rows[factor]
        try:
            rows, source = self._fetch(factor, today, full)
        except ProviderError as error:
            log.warning("Factor en directo no disponible (%s): %s", factor.value, error)
            self._failed.add(factor)
            self._next[factor] = now + FACTOR_TTL
            return
        repository.save_factor(factor.value, _sessions(rows, today), source, now)
        self._rows[factor] = repository.load_factor(factor.value)
        self._failed.discard(factor)
        self._next[factor] = now + FACTOR_TTL

    def _fetch(
        self, factor: Factor, today: date, full: bool
    ) -> tuple[list[tuple[date, Decimal]], str]:
        if factor is Factor.RATES_EUR:
            start = _years_before(today, FULL_YEARS) if full else today - SHORT_DAYS
            return self._rates.rates(start), ecb.SOURCE
        symbol, digits = YAHOO_FACTORS[factor]
        chart = self._charts.chart(symbol, f"{FULL_YEARS}y" if full else SHORT_RANGE)
        step = Decimal(1).scaleb(-digits)
        rows = [(day, value.quantize(step, ROUND_HALF_EVEN)) for day, value in chart.closes]
        return rows, f"yahoo:{symbol}"

    def source_of(self, factor: Factor, day: date) -> str | None:
        """Fuente guardada del cierre de `day` (para la traza)."""
        return next((src for d, _, src in self._rows.get(factor, []) if d == day), None)
