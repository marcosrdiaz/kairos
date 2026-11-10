"""Pre-analiza con Claude los eventos del replay y los deja en la caché (T2-26, D-083).

Con la caché llena, `/demo/reset` con `preload` y los replays del guion no llaman al modelo: la demo
no depende de su latencia ni de que responda, y cada ensayo cuenta la misma cadena causal. Hace
falta `ANTHROPIC_API_KEY`; sin ella, todos salen «respaldo» y no se guarda nada. Repetirlo no
vuelve a llamar al modelo salvo que haya cambiado el prompt o el evento.

    cd backend && uv run python ../scripts/preanalyze_events.py [bce-2025-06 ...]
    docker compose run --rm seed python /scripts/preanalyze_events.py
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("event_ids", nargs="*", help="por defecto, todos los del replay")
    args = parser.parse_args(argv)

    from app.events import service

    results = service.preanalyze(args.event_ids or None)
    for event_id, by_model in results.items():
        print(f"{event_id}: {'analizado por el modelo' if by_model else 'respaldo (sin guardar)'}")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
