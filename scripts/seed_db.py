"""Carga `data/seed` en la base de datos (catálogo de activos y carteras de Laura y Javier).

Idempotente (D-034): el servicio `seed` de Compose lo ejecuta en cada `up`, después de
`alembic upgrade head`. Crea las carteras que falten y no toca las que ya existen; con `--force`
las devuelve a su estado inicial (lo mismo que `POST /demo/reset`).

    docker compose run --rm seed                       # lo hace `make seed`
    cd backend && uv run python ../scripts/seed_db.py [--force]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# En Docker el código está en /app (directorio de trabajo); en local, en <repo>/backend.
for candidate in (Path.cwd(), Path(__file__).resolve().parents[1] / "backend"):
    if (candidate / "app" / "__init__.py").is_file() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))
        break


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true", help="vuelve al estado inicial del seed")
    args = parser.parse_args()

    from app.exposure import service as exposure_service
    from app.portfolio import service

    ids = service.load_seed(force=args.force)
    exposure_service.load_compositions()
    action = "recargadas" if args.force else "listas"
    print(f"seed: carteras {action}: {', '.join(ids)}")


if __name__ == "__main__":
    main()
