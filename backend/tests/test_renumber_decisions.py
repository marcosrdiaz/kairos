"""`scripts/renumber_decisions.py`: numeración de las decisiones `D-XXX`."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "renumber_decisions.py"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("renumber_decisions", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["renumber_decisions"] = module
    spec.loader.exec_module(module)
    return module


script = _load()

HEADER = """# Registro de decisiones

## Cómo se usa

- Escribe la decisión con el ID provisional `D-XXX`.

```
### D-XXX · Título corto
```

## Índice

| ID | Fecha | Título | Estado |
| --- | --- | --- | --- |
"""


def _doc(rows: list[tuple[str, str]], extra: dict[str, str] | None = None) -> str:
    """Documento con índice y entradas; `extra` añade texto a la entrada de ese ID."""
    index = "".join(f"| {i} | 2026-11-08 | {t} | Aceptada |\n" for i, t in rows)
    body = "".join(
        f"\n### {i} · {t}\n- Estado: Aceptada\n{(extra or {}).get(i, '')}" for i, t in rows
    )
    return f"{HEADER}{index}\n---\n{body}"


def _write(root: Path, name: str, text: str) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return path


def _decisions(root: Path) -> str:
    return (root / "docs" / "decisiones.md").read_text(encoding="utf-8")


def _setup(root: Path, rows: list[tuple[str, str]], extra: dict[str, str] | None = None) -> Path:
    return _write(root, "docs/decisiones.md", _doc(rows, extra))


def test_one_placeholder_gets_next_id(tmp_path: Path) -> None:
    _setup(tmp_path, [("D-001", "Uno"), ("D-002", "Dos"), ("D-XXX", "Nueva")])
    report = script.renumber(tmp_path, files=[])
    text = _decisions(tmp_path)
    assert "| D-003 | 2026-11-08 | Nueva |" in text
    assert "### D-003 · Nueva" in text
    assert "D-XXX" in text.split("## Índice")[0]  # la cabecera explica la convención
    assert "D-XXX" not in text.split("## Índice")[1]
    assert report == ["D-XXX → D-003  Nueva"]


def test_several_placeholders_number_in_order_of_appearance(tmp_path: Path) -> None:
    _setup(tmp_path, [("D-007", "Previa"), ("D-XXX", "Primera"), ("D-XXX", "Segunda")])
    script.renumber(tmp_path, files=[])
    text = _decisions(tmp_path)
    assert text.index("### D-008 · Primera") < text.index("### D-009 · Segunda")
    assert "| D-008 | 2026-11-08 | Primera |" in text
    assert "| D-009 | 2026-11-08 | Segunda |" in text


def test_suffixes_keep_branch_order_and_resolve_references(tmp_path: Path) -> None:
    rows = [("D-004", "Previa"), ("D-XXX-a", "Alfa"), ("D-XXX-b", "Beta")]
    _setup(tmp_path, rows, {"D-XXX-b": "- Consecuencias: depende de D-XXX-a.\n"})
    other = _write(tmp_path, "docs/SPEC.md", "Ver D-XXX-b y `D-XXX-a`.\n")
    script.renumber(tmp_path, files=[other])
    text = _decisions(tmp_path)
    assert "### D-005 · Alfa" in text
    assert "### D-006 · Beta" in text
    assert "depende de D-005." in text
    assert other.read_text(encoding="utf-8") == "Ver D-006 y `D-005`.\n"


def test_numbered_decisions_in_other_branches_count_for_next_id(tmp_path: Path) -> None:
    _setup(tmp_path, [("D-010", "Diez"), ("D-XXX", "Nueva")])
    script.renumber(tmp_path, files=[])
    assert "### D-011 · Nueva" in _decisions(tmp_path)


def test_no_placeholders_changes_nothing_and_is_idempotent(tmp_path: Path) -> None:
    path = _setup(tmp_path, [("D-001", "Uno"), ("D-002", "Dos")])
    before = path.read_bytes()
    assert script.renumber(tmp_path, files=[]) == []
    assert path.read_bytes() == before
    _setup(tmp_path, [("D-001", "Uno"), ("D-XXX", "Nueva")])
    script.renumber(tmp_path, files=[])
    after_first = path.read_bytes()
    assert script.renumber(tmp_path, files=[]) == []
    assert path.read_bytes() == after_first


def test_main_prints_and_exits_zero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _setup(tmp_path, [("D-001", "Uno")])
    assert script.main(["--root", str(tmp_path)]) == 0
    assert "Nada que renumerar" in capsys.readouterr().out


def test_repeated_ids_fail(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = _setup(tmp_path, [("D-001", "Uno"), ("D-001", "Otra vez"), ("D-XXX", "Nueva")])
    before = path.read_bytes()
    assert script.main(["--root", str(tmp_path)]) == 1
    assert "D-001" in capsys.readouterr().err
    assert path.read_bytes() == before


def test_repeated_ids_fail_even_without_placeholders(tmp_path: Path) -> None:
    _setup(tmp_path, [("D-002", "Uno"), ("D-002", "Dos")])
    with pytest.raises(script.RenumberError, match="repetidos"):
        script.renumber(tmp_path, files=[])


def test_entry_without_index_row_fails(tmp_path: Path) -> None:
    path = _setup(tmp_path, [("D-001", "Uno"), ("D-XXX", "Nueva")])
    text = path.read_text(encoding="utf-8").replace(
        "| D-XXX | 2026-11-08 | Nueva | Aceptada |\n", ""
    )
    path.write_text(text, encoding="utf-8")
    with pytest.raises(script.RenumberError, match="no cuadran"):
        script.renumber(tmp_path, files=[])


def test_ambiguous_bare_references_are_left_and_reported(tmp_path: Path) -> None:
    _setup(
        tmp_path,
        [("D-001", "Uno"), ("D-XXX", "Primera"), ("D-XXX", "Segunda")],
        {"D-XXX": "- Ver D-XXX.\n"},
    )
    other = _write(tmp_path, "docs/nota.md", "Ver D-XXX.\n")
    report = script.renumber(tmp_path, files=[other])
    assert other.read_text(encoding="utf-8") == "Ver D-XXX.\n"
    assert any("ambiguas" in line for line in report)


def test_single_bare_reference_is_replaced_everywhere(tmp_path: Path) -> None:
    _setup(tmp_path, [("D-001", "Uno"), ("D-XXX", "Nueva")])
    code = _write(tmp_path, "backend/app/x.py", "# ver D-XXX\n")
    script.renumber(tmp_path, files=[code])
    assert code.read_text(encoding="utf-8") == "# ver D-002\n"


def test_convention_files_are_protected(tmp_path: Path) -> None:
    _setup(tmp_path, [("D-001", "Uno"), ("D-XXX", "Nueva")])
    protected = _write(tmp_path, "CLAUDE.md", "Las decisiones nuevas van con D-XXX.\n")
    command = _write(tmp_path, ".claude/commands/decision.md", "Usa D-XXX.\n")
    script.renumber(tmp_path, files=[protected, command])
    assert protected.read_text(encoding="utf-8") == "Las decisiones nuevas van con D-XXX.\n"
    assert command.read_text(encoding="utf-8") == "Usa D-XXX.\n"


def test_crlf_line_endings_are_preserved(tmp_path: Path) -> None:
    text = _doc([("D-001", "Uno"), ("D-XXX", "Nueva")]).replace("\n", "\r\n")
    path = _write(tmp_path, "docs/decisiones.md", text)
    script.renumber(tmp_path, files=[])
    data = path.read_bytes()
    assert b"### D-002" in data
    assert data.count(b"\r\n") == data.count(b"\n")


def test_real_repo_decisions_file_is_consistent() -> None:
    """El fichero real no tiene IDs repetidos ni entradas sin fila de índice."""
    repo = SCRIPT.parent.parent
    lines = (repo / "docs" / "decisiones.md").read_text(encoding="utf-8").splitlines(True)
    start = next(i for i, line in enumerate(lines) if line.startswith("## Índice"))
    script._Plan(lines, start)
