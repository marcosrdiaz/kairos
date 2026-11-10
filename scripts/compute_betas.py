"""`compute_betas.py` (T1-12, T4-03): recalcula `factor_beta` de todo el catálogo.

El cálculo es `app.impact.service.recompute_betas` (T4-03): lee las series de `prices`, así que
en modo demo usa los CSV de `data/prices` (`adj_close`, D-045) y `data/factors`, y en directo lo
guardado en `price` y `factor_close`. Ventana: los últimos `--years` años (3 por defecto) hasta el
último cierre común de los factores, sin pasar del reloj. Los activos de precio fijo se omiten;
los que no se pueden estimar se quedan sin betas (no con las antiguas), así que se puede repetir.
Necesita la tabla `asset` sembrada antes (`seed_db.py`).

En Docker: `make betas`. En local, desde `backend/`:
`uv run python ../scripts/compute_betas.py [--dry-run]`.
"""

from __future__ import annotations

import argparse
import sys

from sqlalchemy.exc import IntegrityError

import app.models  # noqa: F401  (registra todas las tablas: la FK factor_beta → asset)
from app.impact import service as impact_service
from app.impact.betas import BetaEstimate
from app.schemas.common import Factor


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
    parser.add_argument("--years", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true", help="muestra las betas sin escribir")
    args = parser.parse_args(argv)

    try:
        run = impact_service.recompute_betas(years=args.years, save=not args.dry_run)
    except IntegrityError:
        print(
            "error: faltan activos en la tabla `asset`; siembra antes (make seed)", file=sys.stderr
        )
        return 1
    for reason in run.missing.values():
        print(f"aviso: {reason}", file=sys.stderr)
    _print_table(run.estimates)
    if not args.dry_run:
        print(f"factor_beta: {run.rows} filas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
