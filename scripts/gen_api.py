"""`make gen-api` (T0-03): contratos del backend → frontend.

1. Vuelca el OpenAPI de la app a `frontend/src/api/generated/openapi.json`.
2. Genera `frontend/src/api/generated/schema.ts` con openapi-typescript. Cada esquema se exporta
   también como tipo raíz con su nombre: `import type { PortfolioOut } from "./generated/schema"`
   (desde `src/api/`).
3. Sustituye `frontend/src/api/mocks/*.json` por todos los `backend/app/schemas/examples/*.json`
   (variantes incluidas). Copia lo que haya: si faltan esquemas de otras tareas, no falla.

Se ejecuta desde `backend/` con su entorno: `cd backend && uv run python ../scripts/gen_api.py`.
Opciones: `--skip-ts` para no llamar a npx (sin red o sin Node).

openapi-typescript va por `npx` con versión fija y no en `package.json`: pide TypeScript 5 como
peer y el frontend usa TypeScript 6 (ver decisiones). Los ficheros generados van al repo.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
EXAMPLES_DIR = BACKEND / "app" / "schemas" / "examples"
GENERATED_DIR = ROOT / "frontend" / "src" / "api" / "generated"
MOCKS_DIR = ROOT / "frontend" / "src" / "api" / "mocks"

OPENAPI_TS = "openapi-typescript@7.13.0"
OPENAPI_TS_FLAGS = ["--root-types", "--root-types-no-schema-prefix", "--alphabetize"]


def build_openapi() -> dict[str, Any]:
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))
    from app.main import create_app

    spec: dict[str, Any] = create_app().openapi()
    return spec


def write_openapi(spec: dict[str, Any], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "openapi.json"
    text = json.dumps(spec, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def generate_ts(openapi_path: Path, out_dir: Path) -> Path:
    npx = shutil.which("npx")
    if npx is None:
        raise SystemExit(
            "gen-api: no encuentro `npx` (Node). Usa --skip-ts para solo copiar mocks."
        )
    out = out_dir / "schema.ts"
    cmd = [npx, "--yes", OPENAPI_TS, str(openapi_path), "-o", str(out), *OPENAPI_TS_FLAGS]
    subprocess.run(cmd, check=True, cwd=ROOT)
    # openapi-typescript escribe con el fin de línea del sistema; el repo es LF (.gitattributes).
    out.write_text(
        out.read_text(encoding="utf-8").replace("\r\n", "\n"), encoding="utf-8", newline="\n"
    )
    return out


def copy_examples(src_dir: Path, dst_dir: Path) -> list[str]:
    """Deja en `dst_dir` exactamente los `*.json` de `src_dir`. Devuelve los nombres copiados."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    for stale in dst_dir.glob("*.json"):
        stale.unlink()
    copied: list[str] = []
    for src in sorted(src_dir.glob("*.json")):
        json.loads(src.read_text(encoding="utf-8"))  # falla pronto si un ejemplo no es JSON
        shutil.copyfile(src, dst_dir / src.name)
        copied.append(src.name)
    return copied


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--skip-ts", action="store_true", help="no generar schema.ts (sin npx)")
    args = parser.parse_args(argv)

    spec = build_openapi()
    openapi_path = write_openapi(spec, GENERATED_DIR)
    n_schemas = len(spec.get("components", {}).get("schemas", {}))
    print(f"gen-api: {openapi_path.relative_to(ROOT)} ({n_schemas} esquemas)")

    if not args.skip_ts:
        ts_path = generate_ts(openapi_path, GENERATED_DIR)
        print(f"gen-api: {ts_path.relative_to(ROOT)}")

    copied = copy_examples(EXAMPLES_DIR, MOCKS_DIR)
    print(f"gen-api: {len(copied)} mocks en {MOCKS_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
