"""Ejemplos de los contratos: `<Modelo>.json` o `<Modelo>.<variante>.json`.

Son los mocks del backend (`*/mock.py` los cargan con `load`) y del frontend (`make gen-api` los
copia a `frontend/src/api/mocks/`). Todos llevan `"illustrative": true`, que no es parte del
contrato: `load` la quita (D-034).
"""

import json
from pathlib import Path
from typing import Any

EXAMPLES_DIR = Path(__file__).parent
ILLUSTRATIVE_KEY = "illustrative"


def model_name(path: Path) -> str:
    """`PortfolioOut.javier.json` → `PortfolioOut`."""
    return path.name.split(".", 1)[0]


def example_files() -> list[Path]:
    return sorted(EXAMPLES_DIR.glob("*.json"))


def load_raw(name: str) -> Any:
    """JSON tal cual, con la marca `illustrative`. `name` sin `.json`: `"PortfolioOut.javier"`."""
    return json.loads((EXAMPLES_DIR / f"{name}.json").read_text(encoding="utf-8"))


def load(name: str) -> Any:
    """JSON sin la marca `illustrative`, listo para `Model.model_validate`."""
    data = load_raw(name)
    if isinstance(data, dict):
        data.pop(ILLUSTRATIVE_KEY, None)
    return data
