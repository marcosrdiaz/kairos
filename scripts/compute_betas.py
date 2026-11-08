"""`compute_betas.py` (T1-12): recalcula `factor_beta` desde `data/prices` y `data/factors`.

- Activos: los de `data/seed/assets.json` con `price_source` `yahoo:` y CSV en `data/prices/`
  (`date,close,adj_close`; se usa `adj_close`, D-045). Los de precio fijo (`fixed:`) no tienen
  sensibilidad que estimar y se omiten.
- Factores: `data/factors/<FACTOR>.csv` (`date,value`).
- Ventana: los últimos `--years` años (3 por defecto) hasta la última fecha común.
- Cálculo en `app.impact.betas`; escritura en `app.impact.repository`: sustituye las filas de todos
  los activos del catálogo (los que no se pueden estimar se quedan sin betas, no con las antiguas),
  así que se puede repetir. Necesita la tabla `asset` sembrada antes (`seed_db.py`).

En Docker: `make betas`. En local, desde `backend/`:
`uv run python ../scripts/compute_betas.py [--dry-run]`.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy.exc import IntegrityError

import app.models  # noqa: F401  (registra todas las tablas: la FK factor_beta → asset)
from app.impact import repository
from app.impact.betas import BetaEstimate, InsufficientData, Series, estimate_betas
from app.schemas.common import Factor

ROOT = Path(__file__).resolve().parent.parent


def read_series(path: Path, column: str) -> dict[date, Decimal]:
    with path.open(newline="", encoding="utf-8") as fh:
        return {
            date.fromisoformat(row["date"]): Decimal(row[column])
            for row in csv.DictReader(fh)
            if row.get(column)
        }


def load_factors(data_dir: Path) -> dict[Factor, Series]:
    return {f: read_series(data_dir / "factors" / f"{f.value}.csv", "value") for f in Factor}


def _catalog(data_dir: Path) -> list[dict[str, object]]:
    raw = json.loads((data_dir / "seed" / "assets.json").read_text(encoding="utf-8"))
    assets: list[dict[str, object]] = raw["assets"] if isinstance(raw, dict) else raw
    return assets


def catalog_asset_ids(data_dir: Path) -> list[str]:
    return [str(a["id"]) for a in _catalog(data_dir)]


def yahoo_asset_ids(data_dir: Path) -> list[str]:
    return [str(a["id"]) for a in _catalog(data_dir) if str(a["price_source"]).startswith("yahoo:")]


def compute_all(data_dir: Path, years: int) -> tuple[list[BetaEstimate], list[str]]:
    """Estimaciones de todos los activos y avisos de los que no se han podido estimar."""
    factors = load_factors(data_dir)
    last_common = min(max(s) for s in factors.values())
    window_start = last_common - timedelta(days=365 * years)

    estimates: list[BetaEstimate] = []
    warnings: list[str] = []
    for asset_id in yahoo_asset_ids(data_dir):
        path = data_dir / "prices" / f"{asset_id}.csv"
        if not path.exists():
            warnings.append(f"{asset_id}: sin {path.name}")
            continue
        try:
            prices = read_series(path, "adj_close")
            estimates += estimate_betas(asset_id, prices, factors, window_start=window_start)
        except InsufficientData as exc:
            warnings.append(str(exc))
    return estimates, warnings


def _print_table(estimates: list[BetaEstimate]) -> None:
    order = list(Factor)
    print(f"{'asset_id':<14} {'R2':>6} {'n':>5}  " + "  ".join(f"{f.value:>16}" for f in order))
    by_asset: dict[str, dict[Factor, BetaEstimate]] = {}
    for e in estimates:
        by_asset.setdefault(e.asset_id, {})[e.factor] = e
    for asset_id, row in by_asset.items():
        first = next(iter(row.values()))
        cells = "  ".join(
            f"{row[f].beta:>8.3f} se {row[f].std_err:<5.3f}" if f in row else f"{'-':>16}"
            for f in order
        )
        print(f"{asset_id:<14} {first.r2:>6.3f} {first.n_obs:>5}  {cells}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--years", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true", help="muestra las betas sin escribir")
    args = parser.parse_args(argv)

    estimates, warnings = compute_all(args.data_dir, args.years)
    for w in warnings:
        print(f"aviso: {w}", file=sys.stderr)
    _print_table(estimates)
    if not args.dry_run:
        try:
            # Se limpia todo el catálogo: un activo que ya no se puede estimar pierde sus betas
            # antiguas en lugar de conservarlas obsoletas.
            written = repository.replace_betas(estimates, clear=catalog_asset_ids(args.data_dir))
        except IntegrityError:
            msg = "error: faltan activos en la tabla `asset`; siembra antes (make seed)"
            print(msg, file=sys.stderr)
            return 1
        print(f"factor_beta: {written} filas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
