"""`scripts/gen_api.py` (T0-03): volcado del OpenAPI y copia de ejemplos a mocks. Sin npx."""

import importlib.util
import json
import re
from pathlib import Path
from types import ModuleType

import pytest

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


def test_generate_ts_asks_for_npm_ci_when_openapi_typescript_is_not_installed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(gen_api, "FRONTEND", tmp_path)  # sin node_modules
    monkeypatch.setattr(gen_api.shutil, "which", lambda _: "npx")
    with pytest.raises(SystemExit, match=r"npm ci"):
        gen_api.generate_ts(tmp_path / "openapi.json", tmp_path)


def test_generate_ts_uses_the_installed_version_and_never_downloads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = tmp_path / "node_modules" / "openapi-typescript" / "package.json"
    package.parent.mkdir(parents=True)
    package.write_text("{}", encoding="utf-8")
    calls: list[tuple[list[str], Path]] = []

    def fake_run(cmd: list[str], check: bool, cwd: Path) -> None:
        calls.append((cmd, cwd))
        (tmp_path / "schema.ts").write_text("export {};\r\n", encoding="utf-8", newline="")

    monkeypatch.setattr(gen_api, "FRONTEND", tmp_path)
    monkeypatch.setattr(gen_api.shutil, "which", lambda _: "npx")
    monkeypatch.setattr(gen_api.subprocess, "run", fake_run)

    out = gen_api.generate_ts(tmp_path / "openapi.json", tmp_path)

    ((cmd, cwd),) = calls
    assert cmd[:3] == ["npx", "--no-install", "openapi-typescript"]
    assert "--yes" not in cmd and not any("@" in part for part in cmd)  # sin versión ni descarga
    assert cwd == tmp_path  # se ejecuta en frontend/, donde está instalado
    assert out.read_bytes() == b"export {};\n"  # LF aunque el generador escriba CRLF


def test_openapi_typescript_is_pinned_to_an_exact_version() -> None:
    """Versión exacta (sin ^ ni ~): el cliente TS generado es reproducible. Ver decisiones."""
    package = json.loads((gen_api.FRONTEND / "package.json").read_text(encoding="utf-8"))
    version = package["devDependencies"]["openapi-typescript"]
    assert re.fullmatch(r"\d+\.\d+\.\d+", version), version
    # Su peer de TypeScript 5 se resuelve con el TypeScript del proyecto (TS 6).
    assert package["overrides"]["openapi-typescript"] == {"typescript": "$typescript"}
    lock = json.loads((gen_api.FRONTEND / "package-lock.json").read_text(encoding="utf-8"))
    assert lock["packages"]["node_modules/openapi-typescript"]["version"] == version
