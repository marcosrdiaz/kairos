"""`fetch_prices.py` (T1-09): históricos diarios y `observed` de los eventos de replay.

1. Descarga 3 años de cierres diarios:
   - `data/prices/<asset_id>.csv` (`date,close,adj_close`): activos con `price_source` `yahoo:` de
     `data/seed/assets.json`, en la divisa de cotización.
   - `data/factors/<FACTOR>.csv` (`date,value`): series de los factores. `RATES_EUR` es la
     rentabilidad como fracción (`0.0264` = 2,64 %), en la misma unidad que el shock.
2. Calcula `observed` de `data/events/replay/*.json` a partir de esos CSV (D-025): cierre de la
   sesión que recoge el evento frente al cierre anterior.

Se ejecuta desde `backend/` con su entorno:
`cd backend && uv run python ../scripts/fetch_prices.py`.
Con `--observed-only` solo recalcula `observed`, sin red.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import time
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path
from typing import Any

import httpx

from app.core.clock import now
from app.events import observed

ROOT = Path(__file__).resolve().parent.parent
ASSETS_PATH = ROOT / "data" / "seed" / "assets.json"
PRICES_DIR = ROOT / "data" / "prices"
FACTORS_DIR = ROOT / "data" / "factors"
REPLAY_DIR = ROOT / "data" / "events" / "replay"

YEARS = 3
MIN_ROWS = 500  # unos 2 años de sesiones
YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
# Curva AAA del área euro a 10 años: cierre a las 17:00 CET, así que recoge lo que pasa ese día.
ECB_10Y_URL = (
    "https://data-api.ecb.europa.eu/service/data/YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y"
    "?format=csvdata&startPeriod={start}"
)
YAHOO_FACTORS = {
    "EQ_GLOBAL": ("IWDA.AS", 4),  # MSCI World en EUR
    "EQ_US_TECH": ("^NDX", 4),
    "OIL": ("BZ=F", 4),
    "EURUSD": ("EURUSD=X", 6),
}
RATES_FACTOR = "RATES_EUR"
FACTORS = (*YAHOO_FACTORS, RATES_FACTOR)
EVENT_COMPANIES = {"nvda-2025-02": {"NVDA": "US67066G1040"}}

OBSERVED_SOURCE = "data/prices + data/factors, cierre del día frente al cierre anterior"

Series = list[tuple[date, Decimal]]


# --- Descarga ---


def _get(url: str, **kwargs: Any) -> httpx.Response:
    last: httpx.HTTPError | None = None
    for attempt in range(3):
        try:
            response = httpx.get(
                url,
                timeout=40,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0"},
                **kwargs,
            )
            response.raise_for_status()
            return response
        except httpx.HTTPError as error:
            last = error
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"No se pudo descargar {url}: {last}")


def _quantize(value: float | str, digits: int) -> str:
    step = Decimal(1).scaleb(-digits)
    return format(Decimal(str(value)).quantize(step, rounding=ROUND_HALF_EVEN), "f")


def _bar_date(timestamp: int) -> date:
    """Fecha de sesión de una barra diaria de Yahoo.

    Según el mercado, la barra empieza a medianoche local o en la apertura. Sumar 6 h deja siempre
    el mismo día natural en las zonas que usamos (Nueva York, Londres, Ámsterdam, Fráncfort).
    """
    return (datetime.fromtimestamp(timestamp, UTC) + timedelta(hours=6)).date()


def parse_yahoo(payload: dict[str, Any], digits: int, today: date) -> list[tuple[str, str, str]]:
    """Filas `(fecha, close, adj_close)`. Quita huecos, fines de semana y la sesión aún abierta."""
    result = payload["chart"]["result"][0]
    closes = result["indicators"]["quote"][0]["close"]
    adjusted = result["indicators"].get("adjclose", [{"adjclose": closes}])[0]["adjclose"]
    rows: dict[str, tuple[str, str, str]] = {}
    for timestamp, close, adj in zip(result["timestamp"], closes, adjusted, strict=True):
        day = _bar_date(timestamp)
        if close is None or adj is None or day >= today or day.weekday() >= 5:
            continue
        rows[day.isoformat()] = (day.isoformat(), _quantize(close, digits), _quantize(adj, digits))
    return [rows[key] for key in sorted(rows)]


def fetch_yahoo(symbol: str, digits: int, today: date) -> list[tuple[str, str, str]]:
    params = {"range": f"{YEARS}y", "interval": "1d", "includeAdjustedClose": "true"}
    url = YAHOO_URL.format(symbol=symbol)
    rows = parse_yahoo(_get(url, params=params).json(), digits, today)
    if len(rows) < MIN_ROWS:
        raise RuntimeError(f"{symbol}: solo {len(rows)} sesiones")
    return rows


def parse_ecb_rates(text: str, today: date) -> list[tuple[str, str]]:
    """Filas `(fecha, rentabilidad como fracción)`. El BCE publica en porcentaje."""
    rows = []
    for row in csv.DictReader(io.StringIO(text)):
        if row["OBS_VALUE"] and date.fromisoformat(row["TIME_PERIOD"]) < today:
            fraction = Decimal(row["OBS_VALUE"]) / 100
            rows.append((row["TIME_PERIOD"], _quantize(str(fraction), 12)))
    return sorted(rows)


def _write_csv(path: Path, header: tuple[str, ...], rows: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def download_assets(ids: set[str], today: date) -> None:
    """Solo los precios de `ids` (activos nuevos del catálogo, T4-26), sin tocar factores ni el
    resto de CSV: así las cifras de la demo no cambian. `today` excluido, como en `download`."""
    assets = json.loads(ASSETS_PATH.read_text(encoding="utf-8"))["assets"]
    unknown = ids - {a["id"] for a in assets}
    if unknown:
        raise SystemExit(f"no están en assets.json: {sorted(unknown)}")
    for asset in assets:
        source = asset["price_source"]
        if asset["id"] in ids and source.startswith("yahoo:"):
            rows = fetch_yahoo(source.removeprefix("yahoo:"), 4, today)
            _write_csv(PRICES_DIR / f"{asset['id']}.csv", ("date", "close", "adj_close"), rows)
            print(f"precios: {asset['id']} {len(rows)} sesiones hasta {rows[-1][0]}")


def download(today: date) -> None:
    assets = json.loads(ASSETS_PATH.read_text(encoding="utf-8"))["assets"]
    for asset in assets:
        source = asset["price_source"]
        if source.startswith("yahoo:"):
            rows = fetch_yahoo(source.removeprefix("yahoo:"), 4, today)
            _write_csv(PRICES_DIR / f"{asset['id']}.csv", ("date", "close", "adj_close"), rows)
            print(f"precios: {asset['id']} {len(rows)} sesiones hasta {rows[-1][0]}")

    for factor, (symbol, digits) in YAHOO_FACTORS.items():
        rows = fetch_yahoo(symbol, digits, today)
        _write_csv(FACTORS_DIR / f"{factor}.csv", ("date", "value"), [r[:2] for r in rows])
        print(f"factor: {factor} {len(rows)} sesiones hasta {rows[-1][0]}")

    start = today - timedelta(days=YEARS * 365)
    rates = parse_ecb_rates(_get(ECB_10Y_URL.format(start=start.isoformat())).text, today)
    if len(rates) < MIN_ROWS:
        raise RuntimeError(f"{RATES_FACTOR}: solo {len(rates)} sesiones")
    _write_csv(FACTORS_DIR / f"{RATES_FACTOR}.csv", ("date", "value"), rates)
    print(f"factor: {RATES_FACTOR} {len(rates)} sesiones hasta {rates[-1][0]}")


# --- `observed` ---


reaction_date = observed.reaction_date
"""La lógica de `observed` vive en `app/events/observed.py` (T4-04): la comparte el backend."""


def series_change(series: Series, day: date, absolute: bool = False) -> Decimal:
    """Variación de la primera sesión desde `day` frente a la anterior (absoluta o relativa).
    Aquí falla si falta esa sesión o la anterior: el replay no admite eventos pendientes."""
    change = observed.series_change(series, day, absolute)
    if change is None:
        raise ValueError(f"No hay sesión desde {day} con una sesión anterior")
    return change


def load_series(path: Path, column: str) -> Series:
    with path.open(encoding="utf-8", newline="") as handle:
        return [(date.fromisoformat(r["date"]), Decimal(r[column])) for r in csv.DictReader(handle)]


def compute_observed(event: dict[str, Any]) -> dict[str, dict[str, str]]:
    occurred_at = datetime.fromisoformat(event["occurred_at"].replace("Z", "+00:00"))
    day = reaction_date(occurred_at)
    factors = {
        factor: format(
            series_change(
                load_series(FACTORS_DIR / f"{factor}.csv", "value"),
                day,
                absolute=factor == RATES_FACTOR,
            ),
            "f",
        )
        for factor in FACTORS
    }
    companies = {
        key: format(series_change(load_series(PRICES_DIR / f"{asset}.csv", "close"), day), "f")
        for key, asset in EVENT_COMPANIES.get(event["id"], {}).items()
    }
    return {"factors": factors, "companies": companies}


def with_observed(event: dict[str, Any]) -> dict[str, Any]:
    """Copia del evento con `observed` tras `source_urls`, sin tocar el resto."""
    observed = {"observed": compute_observed(event), "observed_source": OBSERVED_SOURCE}
    out: dict[str, Any] = {}
    for key, value in event.items():
        if key in observed:
            continue
        out[key] = value
        if key == "source_urls":
            out.update(observed)
    return out


def update_events() -> None:
    for path in sorted(REPLAY_DIR.glob("*.json")):
        event = with_observed(json.loads(path.read_text(encoding="utf-8")))
        text = json.dumps(event, indent=2, ensure_ascii=False) + "\n"
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"observed: {path.stem} {event['observed']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--observed-only", action="store_true", help="no descargar, sin red")
    parser.add_argument(
        "--assets",
        help="solo estos activos (ids separados por comas), sin factores ni eventos (T4-26)",
    )
    parser.add_argument(
        "--until",
        type=date.fromisoformat,
        help="último día que se descarga (AAAA-MM-DD); por defecto, la víspera de hoy",
    )
    args = parser.parse_args(argv)
    if args.assets:
        ids = {a.strip() for a in args.assets.split(",") if a.strip()}
        until = args.until or now().date() - timedelta(days=1)
        download_assets(ids, until + timedelta(days=1))
        return 0
    if not args.observed_only:
        download(now().date())
    update_events()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
