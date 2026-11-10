"""Actualización diaria tras el cierre: guarda los cierres de los activos en cartera, el EUR/USD y
los 5 factores sin que nadie abra la app (T4-02).

Solo en producción (`MARKET_DATA_PROVIDER=yahoo`); en modo demo no hace nada y termina. Usa los
proveedores en directo del backend (T2-24 y T4-01): piden a Yahoo y al BCE y guardan en `price`,
`fx_rate` y `factor_close`. Guardar es idempotente, así que repetirlo no duplica filas. Un fallo
de un activo o factor se registra y no para el resto ni el backend.

    python /scripts/daily_update.py --loop [--at 22:30]   # servicio `updater` de Compose
    cd backend && uv run python ../scripts/daily_update.py --once

Por defecto corre de lunes a viernes a las 22:30 UTC: después del cierre de Nueva York (21:00
UTC en invierno, 20:00 en verano), que es el último de los mercados del catálogo.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time as time_module
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any

# En Docker el código está en /app (directorio de trabajo); en local, en <repo>/backend.
for candidate in (Path.cwd(), Path(__file__).resolve().parents[1] / "backend"):
    if (candidate / "app" / "__init__.py").is_file() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))
        break

log = logging.getLogger("daily_update")

DEFAULT_AT = time(22, 30)
FX_PAIRS = ("EURUSD",)
_STALE_MARK = "no respondió"


@dataclass
class Report:
    updated: list[str] = field(default_factory=list)
    failed: dict[str, str] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    """Eventos pendientes de cierre que se han podido medir y procesar (T4-04)."""


def _update(report: Report, key: str, fetch: Callable[[], str]) -> None:
    """`fetch` pide el valor y devuelve la etiqueta de su fuente. Un fallo se apunta y no para al
    resto; un valor servido de lo guardado porque el proveedor falló también cuenta como fallo."""
    try:
        label = fetch()
    except Exception as error:
        report.failed[key] = str(error) or type(error).__name__
        return
    if _STALE_MARK in label:
        report.failed[key] = label
    else:
        report.updated.append(key)


def update_once() -> Report:
    """Pide y guarda el último cierre de cada activo en cartera, del EUR/USD y de cada factor, y
    después procesa los eventos pendientes de cierre que ya se pueden medir."""
    from app.portfolio import service as portfolio_service
    from app.prices import service as prices_service
    from app.schemas.common import Factor

    report = Report()
    for asset_id in portfolio_service.held_asset_ids():
        if prices_service.has_market_prices(asset_id):  # sin los de valor fijo (depósitos, planes)
            _update(
                report, f"asset:{asset_id}", lambda a=asset_id: _label(prices_service.latest(a))
            )
    for pair in FX_PAIRS:
        _update(report, f"fx:{pair}", lambda p=pair: _label(prices_service.fx_quote(p)))
    for factor in Factor:
        _update(
            report,
            f"factor:{factor.value}",
            lambda f=factor: _label(prices_service.factor_latest(f)),
        )
    from app.events import service as events_service

    try:
        report.events = events_service.process_pending()  # con los cierres ya guardados
    except Exception as error:
        report.failed["events:pending"] = str(error) or type(error).__name__
    return report


def _label(value: Any) -> str:
    label: str = value.source.label
    return label


def next_run(now: datetime, at: time) -> datetime:
    """Próxima ejecución estrictamente posterior a `now`: hoy o el siguiente día laborable a la
    hora `at` (UTC)."""
    day = now.date()
    while True:
        candidate = datetime.combine(day, at, tzinfo=now.tzinfo)
        if candidate > now and candidate.weekday() < 5:
            return candidate
        day += timedelta(days=1)


def parse_at(text: str) -> time:
    hours, minutes = text.split(":")
    return time(int(hours), int(minutes))


def _run_and_log() -> None:
    try:
        report = update_once()
    except Exception:
        log.exception("Actualización diaria: error inesperado; se reintenta en la próxima")
        return
    log.info(
        "Actualización diaria: %d al día, %d con fallo", len(report.updated), len(report.failed)
    )
    for key, reason in sorted(report.failed.items()):
        log.warning("  %s: %s", key, reason)
    if report.events:
        log.info("Eventos procesados tras el cierre: %s", ", ".join(report.events))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--once", action="store_true", help="una actualización y termina")
    mode.add_argument("--loop", action="store_true", help="cada día laborable a la hora --at")
    parser.add_argument("--at", type=parse_at, default=DEFAULT_AT, help="HH:MM en UTC")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    from app.config import get_settings
    from app.core import clock

    if get_settings().market_data_provider != "yahoo":
        log.info("Modo demo (precios offline): no hay nada que actualizar")
        return 0
    if args.once:
        _run_and_log()
        return 0
    while True:
        due = next_run(clock.now(), args.at)
        log.info("Próxima actualización: %s", due.isoformat())
        time_module.sleep(max(0.0, (due - clock.now()).total_seconds()))
        _run_and_log()


if __name__ == "__main__":
    sys.exit(main())
