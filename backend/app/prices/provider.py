"""Proveedores de precios: de dónde salen los cierres diarios y los tipos de cambio.

`OfflineCsvProvider` (modo por defecto, D-014) lee los CSV de T1-09 (D-045):

- `data/prices/<asset_id>.csv` con cabecera `date,close,adj_close`: se usa `close`, el cierre
  diario (o VL) en la divisa del activo.
- `data/factors/<PAR>.csv` con cabecera `date,value`: `EURUSD` = dólares por un euro.

Fechas `AAAA-MM-DD`; decimales con punto. El orden de las filas da igual y las líneas vacías se
ignoran. Un fichero que no existe equivale a una serie vacía.
"""

import csv
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Protocol, runtime_checkable

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
"""En local, `<repo>/data`; en Docker, `/data` (montado en Compose)."""
DEFAULT_PRICES_DIR = DATA_DIR / "prices"
DEFAULT_FACTORS_DIR = DATA_DIR / "factors"


@dataclass(frozen=True)
class PricePoint:
    day: date
    value: Decimal
    at: datetime | None = None
    """Instante del precio si no es un cierre diario (precio en directo); si no, las 00:00 UTC."""
    stale: bool = False
    """Último precio guardado porque el proveedor en directo no respondió (D-065)."""


class PriceProvider(Protocol):
    def closes(self, asset_id: str) -> list[PricePoint]:
        """Cierres del activo en orden ascendente de fecha. Vacío si no hay datos."""
        ...

    def fx_closes(self, pair: str) -> list[PricePoint]:
        """Tipos del par (`EURUSD`) en orden ascendente de fecha. Vacío si no hay datos."""
        ...


@runtime_checkable
class AdjustedPriceProvider(Protocol):
    """Proveedor que además da cierres ajustados por dividendos (T4-03). Opcional: quien no lo
    implementa sirve sus cierres para las betas (`service.beta_closes`)."""

    def adjusted_closes(self, asset_id: str) -> list[PricePoint]:
        """Cierres ajustados del activo en orden ascendente de fecha. Vacío si no hay datos."""
        ...


def _read_series(path: Path, value_column: str) -> list[PricePoint]:
    if not path.is_file():
        return []
    points: list[PricePoint] = []
    with path.open(encoding="utf-8", newline="") as fh:
        for n, row in enumerate(csv.DictReader(fh), start=2):
            raw_day, raw_value = (row.get("date") or "").strip(), (row.get(value_column) or "")
            if not raw_day and not raw_value.strip():
                continue
            try:
                value = Decimal(raw_value.strip())
                if not value.is_finite() or value <= 0:
                    raise InvalidOperation
                points.append(PricePoint(day=date.fromisoformat(raw_day), value=value))
            except (ValueError, InvalidOperation) as exc:
                raise ValueError(f"{path.name}, línea {n}: fila no válida {row!r}") from exc
    return sorted(points, key=lambda p: p.day)


class OfflineCsvProvider:
    """Lee los CSV una vez por fichero y los guarda en memoria."""

    def __init__(
        self, prices_dir: Path = DEFAULT_PRICES_DIR, factors_dir: Path = DEFAULT_FACTORS_DIR
    ) -> None:
        self.prices_dir = prices_dir
        self.factors_dir = factors_dir
        self._cache: dict[tuple[Path, str], list[PricePoint]] = {}

    def _series(self, path: Path, value_column: str) -> list[PricePoint]:
        key = (path, value_column)
        if key not in self._cache:
            self._cache[key] = _read_series(path, value_column)
        return self._cache[key]

    def closes(self, asset_id: str) -> list[PricePoint]:
        return list(self._series(self.prices_dir / f"{asset_id}.csv", "close"))

    def adjusted_closes(self, asset_id: str) -> list[PricePoint]:
        """`adj_close` de los CSV: la serie con la que se estiman las betas (D-045)."""
        return list(self._series(self.prices_dir / f"{asset_id}.csv", "adj_close"))

    def fx_closes(self, pair: str) -> list[PricePoint]:
        return list(self._series(self.factors_dir / f"{pair}.csv", "value"))
