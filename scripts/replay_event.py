"""Inyecta un evento del modo replay sin pasar por HTTP (`make replay` usa la API).

cd backend && uv run python ../scripts/replay_event.py bce-2025-06 [--silent]
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
    parser.add_argument("event_id")
    parser.add_argument("--silent", action="store_true", help="no genera avisos")
    args = parser.parse_args()

    from app.events import service
    from app.schemas.events import ReplayRequest

    result = service.replay(args.event_id, ReplayRequest(silent=args.silent))
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
