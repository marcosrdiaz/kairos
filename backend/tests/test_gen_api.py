"""`scripts/gen_api.py` (T0-03): volcado del OpenAPI y copia de ejemplos a mocks. Sin npx."""

import importlib.util
import json
from pathlib import Path
from types import ModuleType

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "gen_api.py"


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("gen_api", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen_api = _load_script()


def test_copy_examples_replaces_stale_mocks_and_keeps_variants(tmp_path: Path) -> None:
    src = tmp_path / "examples"
    dst = tmp_path / "mocks"
    src.mkdir()
    dst.mkdir()
    (src / "PortfolioOut.json").write_text('{"id": "laura"}', encoding="utf-8")
    (src / "PortfolioOut.javier.json").write_text('{"id": "javier"}', encoding="utf-8")
    (src / "__init__.py").write_text("", encoding="utf-8")
    (dst / "Removed.json").write_text("{}", encoding="utf-8")

    copied = gen_api.copy_examples(src, dst)

    assert copied == ["PortfolioOut.javier.json", "PortfolioOut.json"]
    assert sorted(p.name for p in dst.iterdir()) == copied
    assert json.loads((dst / "PortfolioOut.javier.json").read_text(encoding="utf-8")) == {
        "id": "javier"
    }


def test_copy_examples_with_empty_source_leaves_no_mocks(tmp_path: Path) -> None:
    src = tmp_path / "examples"
    src.mkdir()
    assert gen_api.copy_examples(src, tmp_path / "mocks") == []


def test_openapi_is_written_deterministically_with_api_prefix(tmp_path: Path) -> None:
    spec = gen_api.build_openapi()
    path = gen_api.write_openapi(spec, tmp_path)
    first = path.read_bytes()
    gen_api.write_openapi(gen_api.build_openapi(), tmp_path)

    assert path.read_bytes() == first
    assert b"\r\n" not in first
    assert all(route.startswith("/api/v1/") for route in spec["paths"])
    assert "PortfolioOut" in spec["components"]["schemas"]


def test_every_routed_schema_example_is_copied() -> None:
    """Cada ejemplo del repo acaba en mocks: el script no filtra por lo que está en el OpenAPI."""
    names = {p.name for p in gen_api.EXAMPLES_DIR.glob("*.json")}
    assert "PortfolioOut.json" in names
    assert "TraceOut.json" in names  # aún sin ruta, pero su mock sí se copia
