"""`scripts/renumber_decisions.py`: numeración de las decisiones `D-XXX` (un fichero cada una)."""

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "renumber_decisions.py"
ROOT = SCRIPT.parents[1]


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

- Las nuevas llevan el ID provisional `D-XXX` en `docs/decisiones/`.

## Índice

<!-- INDICE:INICIO -->
<!-- INDICE:FIN -->
"""
INDEX_HEAD = "| ID | Fecha | Título | Estado |"

Spec = tuple[str, str, str]  # (token, slug, título)


def _write(root: Path, name: str, text: str) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return path


def _read(root: Path, name: str) -> str:
    return (root / name).read_text(encoding="utf-8")


def _decision(
    root: Path, spec: Spec, *, state: str = "Aceptada", extra: str = "", eol: str = "\n"
) -> Path:
    token, slug, title = spec
    body = (
        f"### {token} · {title}\n- Fecha: 2026-11-08 10:00 · Autor: t · Estado: {state}\n"
        f"- Contexto: x\n{extra}"
    )
    return _write(root, f"docs/decisiones/{token}-{slug}.md", body.replace("\n", eol))


def _setup(root: Path, *specs: Spec, index: bool = True) -> None:
    """`decisiones.md` con cabecera, las decisiones indicadas y el índice ya generado."""
    _write(root, "docs/decisiones.md", HEADER)
    for spec in specs:
        _decision(root, spec)
    if index:
        script.write_index(root)


def _index(root: Path) -> list[str]:
    return [
        line for line in _read(root, "docs/decisiones.md").splitlines() if line.startswith("| ")
    ]


def test_one_placeholder_gets_next_id_and_file_is_renamed(tmp_path: Path) -> None:
    _setup(tmp_path, ("D-001", "uno", "Uno"), ("D-002", "dos", "Dos"), ("D-XXX", "nueva", "Nueva"))
    report = script.renumber(tmp_path, files=[])
    assert not (tmp_path / "docs/decisiones/D-XXX-nueva.md").exists()
    assert _read(tmp_path, "docs/decisiones/D-003-nueva.md").startswith("### D-003 · Nueva\n")
    assert "| [D-003](decisiones/D-003-nueva.md) | 2026-11-08 | Nueva | Aceptada |" in _index(
        tmp_path
    )
    assert "D-XXX → D-003  Nueva" in report


def test_several_placeholders_number_in_order_of_slug(tmp_path: Path) -> None:
    _setup(tmp_path, ("D-001", "uno", "Uno"), ("D-XXX", "zeta", "Zeta"), ("D-XXX", "alfa", "Alfa"))
    script.renumber(tmp_path, files=[])
    assert (tmp_path / "docs/decisiones/D-002-alfa.md").exists()
    assert (tmp_path / "docs/decisiones/D-003-zeta.md").exists()


def test_suffixes_keep_branch_order_and_resolve_references(tmp_path: Path) -> None:
    _setup(tmp_path, ("D-004", "previa", "Previa"), index=False)
    _decision(tmp_path, ("D-XXX-b", "beta", "Beta"), extra="- Depende de D-XXX-a.\n")
    _decision(tmp_path, ("D-XXX-a", "alfa", "Alfa"))
    other = _write(tmp_path, "docs/SPEC.md", "Ver D-XXX-b y `D-XXX-a`.\n")
    script.renumber(tmp_path, files=[other])
    assert _read(tmp_path, "docs/decisiones/D-005-alfa.md").startswith("### D-005 · Alfa\n")
    beta = _read(tmp_path, "docs/decisiones/D-006-beta.md")
    assert beta.startswith("### D-006 · Beta\n") and "Depende de D-005." in beta
    assert _read(tmp_path, "docs/SPEC.md") == "Ver D-006 y `D-005`.\n"
    assert [r.split("|")[1].strip() for r in _index(tmp_path)[2:]] == [
        "[D-004](decisiones/D-004-previa.md)",
        "[D-005](decisiones/D-005-alfa.md)",
        "[D-006](decisiones/D-006-beta.md)",
    ]


def test_numbered_decisions_in_other_branches_count_for_next_id(tmp_path: Path) -> None:
    _setup(tmp_path, ("D-010", "diez", "Diez"), ("D-XXX", "nueva", "Nueva"))
    script.renumber(tmp_path, files=[])
    assert (tmp_path / "docs/decisiones/D-011-nueva.md").exists()


def test_index_is_sorted_and_lists_only_numbered_decisions(tmp_path: Path) -> None:
    _setup(tmp_path, ("D-002", "dos", "Dos"), ("D-001", "uno", "Uno"), ("D-XXX", "aun", "Aún no"))
    rows = _index(tmp_path)
    assert rows[0] == INDEX_HEAD
    assert [r.split("|")[1].strip()[:7] for r in rows[2:]] == ["[D-001]", "[D-002]"]


def test_state_change_in_an_old_file_is_picked_up_by_the_index(tmp_path: Path) -> None:
    _setup(tmp_path, ("D-001", "uno", "Uno"), ("D-002", "dos", "Dos"))
    _decision(tmp_path, ("D-001", "uno", "Uno"), state="Sustituida por D-002")
    assert script.renumber(tmp_path, files=[]) == ["Índice de decisiones regenerado"]
    assert "| Uno | Sustituida por D-002 |" in _read(tmp_path, "docs/decisiones.md")


def test_no_placeholders_changes_nothing_and_is_idempotent(tmp_path: Path) -> None:
    _setup(tmp_path, ("D-001", "uno", "Uno"), ("D-002", "dos", "Dos"))
    before = _read(tmp_path, "docs/decisiones.md")
    assert script.renumber(tmp_path, files=[]) == []
    assert _read(tmp_path, "docs/decisiones.md") == before
    script.renumber(tmp_path, files=[])
    assert _read(tmp_path, "docs/decisiones.md") == before


def test_index_only_regenerates_and_leaves_placeholders_alone(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _setup(tmp_path, ("D-001", "uno", "Uno"), ("D-XXX", "nueva", "Nueva"), index=False)
    assert script.main(["--root", str(tmp_path), "--index-only"]) == 0
    assert "Índice regenerado" in capsys.readouterr().out
    assert (tmp_path / "docs/decisiones/D-XXX-nueva.md").exists()
    assert len(_index(tmp_path)) == 3


def test_main_prints_and_exits_zero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _setup(tmp_path, ("D-001", "uno", "Uno"), ("D-XXX", "nueva", "Nueva"))
    assert script.main(["--root", str(tmp_path)]) == 0
    assert "D-XXX → D-002  Nueva" in capsys.readouterr().out
    assert script.main(["--root", str(tmp_path)]) == 0
    assert "Nada que renumerar." in capsys.readouterr().out


def test_repeated_ids_between_files_fail_and_write_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _setup(
        tmp_path,
        ("D-005", "uno", "Uno"),
        ("D-005", "otro", "Otro"),
        ("D-XXX", "n", "Nueva"),
        index=False,
    )
    before = _read(tmp_path, "docs/decisiones.md")
    assert script.main(["--root", str(tmp_path)]) == 1
    assert "IDs repetidos entre ficheros: D-005" in capsys.readouterr().err
    assert (tmp_path / "docs/decisiones/D-XXX-n.md").exists()
    assert _read(tmp_path, "docs/decisiones.md") == before


def test_repeated_suffix_between_branches_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _setup(tmp_path, ("D-001", "uno", "Uno"), index=False)
    _decision(tmp_path, ("D-XXX-a", "una", "Una"))
    _decision(tmp_path, ("D-XXX-a", "otra", "Otra"))
    assert script.main(["--root", str(tmp_path)]) == 1
    assert "Sufijos repetidos: D-XXX-a" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("name", "text", "message"),
    [
        ("D-1-mal.md", "### D-1 · X\n", "el nombre debe ser"),
        ("D-002-Con-Mayusculas.md", "### D-002 · X\n", "el nombre debe ser"),
        ("D-002-sin-tilde-é.md", "### D-002 · X\n", "el nombre debe ser"),
        ("D-002-dos.md", "### D-003 · X\n- Fecha: 2026-11-08 · Estado: A\n", "primera línea"),
        ("D-002-dos.md", "### D-002 · X\n- Autor: yo\n", "falta «- Fecha"),
    ],
)
def test_malformed_files_fail_with_a_clear_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], name: str, text: str, message: str
) -> None:
    _setup(tmp_path, ("D-001", "uno", "Uno"), index=False)
    _write(tmp_path, f"docs/decisiones/{name}", text)
    assert script.main(["--root", str(tmp_path)]) == 1
    assert message in capsys.readouterr().err


def test_missing_index_markers_fail_before_writing_anything(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write(tmp_path, "docs/decisiones.md", "# Sin marcadores\n")
    _decision(tmp_path, ("D-XXX", "nueva", "Nueva"))
    assert script.main(["--root", str(tmp_path)]) == 1
    assert "marcadores" in capsys.readouterr().err
    assert (tmp_path / "docs/decisiones/D-XXX-nueva.md").exists()


def test_ambiguous_bare_references_are_left_and_reported(tmp_path: Path) -> None:
    _setup(tmp_path, ("D-001", "uno", "Uno"), index=False)
    _decision(tmp_path, ("D-XXX", "primera", "Primera"), extra="- Ver D-XXX.\n")
    _decision(tmp_path, ("D-XXX", "segunda", "Segunda"))
    other = _write(tmp_path, "docs/nota.md", "Ver D-XXX.\n")
    report = script.renumber(tmp_path, files=[other])
    assert _read(tmp_path, "docs/nota.md") == "Ver D-XXX.\n"
    assert "Ver D-XXX." in _read(tmp_path, "docs/decisiones/D-002-primera.md")
    assert any("ambiguas" in line for line in report)


def test_single_bare_reference_is_replaced_in_decision_and_other_files(tmp_path: Path) -> None:
    _setup(tmp_path, ("D-001", "uno", "Uno"), index=False)
    _decision(tmp_path, ("D-XXX", "nueva", "Nueva"), extra="- Ver D-XXX.\n")
    code = _write(tmp_path, "backend/app/x.py", "# ver D-XXX\n")
    script.renumber(tmp_path, files=[code])
    assert code.read_text(encoding="utf-8") == "# ver D-002\n"
    assert "- Ver D-002.\n" in _read(tmp_path, "docs/decisiones/D-002-nueva.md")


def test_placeholder_in_file_outside_the_diff_is_not_renumbered(tmp_path: Path) -> None:
    """El tablero cita decisiones de otros PRs sin mergear: no es del commit que numera."""
    _setup(tmp_path, ("D-001", "uno", "Uno"), ("D-XXX", "nueva", "Nueva"))
    in_diff = _write(tmp_path, "docs/SPEC.md", "Ver D-XXX.\n")
    outside = _write(tmp_path, "docs/TABLERO.md", "Nota: decisión D-XXX en otro PR.\n")
    report = script.renumber(tmp_path, files=[in_diff])
    assert in_diff.read_text(encoding="utf-8") == "Ver D-002.\n"
    assert outside.read_text(encoding="utf-8") == "Nota: decisión D-XXX en otro PR.\n"
    assert any("docs/TABLERO.md" in line and "no se toca" in line for line in report)


def test_no_files_only_processes_the_decisions(tmp_path: Path) -> None:
    _setup(tmp_path, ("D-001", "uno", "Uno"), ("D-XXX", "nueva", "Nueva"))
    other = _write(tmp_path, "docs/nota.md", "Ver D-XXX.\n")
    script.main(["--root", str(tmp_path)])
    assert (tmp_path / "docs/decisiones/D-002-nueva.md").exists()
    assert other.read_text(encoding="utf-8") == "Ver D-XXX.\n"


def test_convention_files_and_numbered_decisions_are_protected(tmp_path: Path) -> None:
    _setup(tmp_path, ("D-001", "uno", "Uno"), ("D-XXX", "nueva", "Nueva"))
    protected = _write(tmp_path, "CLAUDE.md", "Las decisiones nuevas van con `D-XXX`.\n")
    command = _write(tmp_path, ".claude/commands/decision.md", "Usa D-XXX.\n")
    prose = _decision(tmp_path, ("D-001", "uno", "Uno"), extra="- El ID provisional es D-XXX.\n")
    script.renumber(tmp_path, files=[protected, command, prose])
    assert protected.read_text(encoding="utf-8") == "Las decisiones nuevas van con `D-XXX`.\n"
    assert command.read_text(encoding="utf-8") == "Usa D-XXX.\n"
    assert "provisional es D-XXX." in prose.read_text(encoding="utf-8")


def test_crlf_line_endings_of_a_decision_are_preserved(tmp_path: Path) -> None:
    _setup(tmp_path, ("D-001", "uno", "Uno"), index=False)
    _decision(tmp_path, ("D-XXX", "nueva", "Nueva"), extra="- Ver D-XXX.\n", eol="\r\n")
    script.renumber(tmp_path, files=[])
    raw = (tmp_path / "docs/decisiones/D-002-nueva.md").read_bytes()
    assert raw.startswith(b"### D-002 \xc2\xb7 Nueva\r\n") and b"Ver D-002.\r\n" in raw
    assert raw.count(b"\n") == raw.count(b"\r\n")


def _git(root: Path, *args: str) -> str:
    env = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
        "PATH": os.environ["PATH"],
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
    }
    out = subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, env=env)
    return out.stdout.decode().strip()


def _commit(root: Path, message: str) -> str:
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", message)
    return _git(root, "rev-parse", "HEAD")


def _repo_with_base_and_push(
    root: Path, base: list[Spec], pushed: list[Spec], refs: dict[str, str] | None = None
) -> tuple[str, str]:
    """Commit `base` (con índice) y luego un push que añade `pushed` y escribe `refs`."""
    _git(root, "init", "-q")
    _setup(root, *base)
    before = _commit(root, "base")
    for spec in pushed:
        _decision(root, spec)
    for name, text in (refs or {}).items():
        _write(root, name, text)
    return before, _commit(root, "push")


def test_main_with_before_after_uses_only_the_files_of_that_push(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _setup(tmp_path, ("D-001", "uno", "Uno"))
    tablero = _write(tmp_path, "docs/TABLERO.md", "Otro PR: D-XXX.\n")
    before = _commit(tmp_path, "base")
    _decision(tmp_path, ("D-XXX", "nueva", "Nueva"))
    spec = _write(tmp_path, "docs/SPEC.md", "Ver D-XXX.\n")
    after = _commit(tmp_path, "push")
    assert script.main(["--root", str(tmp_path), "--before", before, "--after", after]) == 0
    assert (tmp_path / "docs/decisiones/D-002-nueva.md").exists()
    assert spec.read_text(encoding="utf-8") == "Ver D-002.\n"
    assert tablero.read_text(encoding="utf-8") == "Otro PR: D-XXX.\n"
    assert "decisiones/D-002-nueva.md" in _git(
        tmp_path, "ls-files"
    )  # git mv: renombrado en el índice
    assert "D-XXX-nueva" not in _git(tmp_path, "ls-files")


def test_stale_placeholders_from_a_failed_run_do_not_make_the_new_reference_ambiguous(
    tmp_path: Path,
) -> None:
    """Incidente del #24: la Action del #23 no corrió y sus D-XXX seguían sin numerar."""
    stale = [
        ("D-001", "uno", "Uno"),
        ("D-XXX", "vieja-a", "Vieja A"),
        ("D-XXX", "vieja-b", "Vieja B"),
    ]
    before, after = _repo_with_base_and_push(
        tmp_path, stale, [("D-XXX", "nueva", "Nueva")], {"backend/tests/x.py": "# (D-XXX)\n"}
    )
    assert script.main(["--root", str(tmp_path), "--before", before, "--after", after]) == 0
    assert (tmp_path / "docs/decisiones/D-002-vieja-a.md").exists()
    assert (tmp_path / "docs/decisiones/D-003-vieja-b.md").exists()
    assert (tmp_path / "docs/decisiones/D-004-nueva.md").exists()
    assert (tmp_path / "backend/tests/x.py").read_text(encoding="utf-8") == "# (D-004)\n"


def test_two_placeholders_added_by_the_same_push_leave_bare_references_ambiguous(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    before, after = _repo_with_base_and_push(
        tmp_path,
        [("D-001", "uno", "Uno")],
        [("D-XXX", "una", "Una"), ("D-XXX", "otra", "Otra")],
        {"docs/SPEC.md": "Ver D-XXX.\n"},
    )
    code = script.main(["--root", str(tmp_path), "--before", before, "--after", after])
    captured = capsys.readouterr()
    assert code == script.EXIT_AMBIGUOUS == 2
    assert _read(tmp_path, "docs/SPEC.md") == "Ver D-XXX.\n"
    assert "ambiguas" in captured.out and "sin numerar" in captured.err
    # lo que sí se pudo numerar queda escrito (la Action lo commitea antes de fallar)
    assert (tmp_path / "docs/decisiones/D-002-otra.md").exists()
    assert (tmp_path / "docs/decisiones/D-003-una.md").exists()


def test_push_without_new_placeholders_does_not_resolve_references_to_old_ones(
    tmp_path: Path,
) -> None:
    """Una D-XXX vieja se numera, pero una referencia nueva sin entrada nueva no es suya."""
    stale = [("D-001", "uno", "Uno"), ("D-XXX", "vieja", "Vieja")]
    before, after = _repo_with_base_and_push(tmp_path, stale, [], {"docs/SPEC.md": "Ver D-XXX.\n"})
    code = script.main(["--root", str(tmp_path), "--before", before, "--after", after])
    assert code == script.EXIT_AMBIGUOUS
    assert (tmp_path / "docs/decisiones/D-002-vieja.md").exists()
    assert _read(tmp_path, "docs/SPEC.md") == "Ver D-XXX.\n"


def test_ambiguous_reference_inside_a_decision_also_exits_nonzero(tmp_path: Path) -> None:
    _setup(tmp_path, ("D-001", "uno", "Uno"), index=False)
    _decision(tmp_path, ("D-XXX", "primera", "Primera"), extra="- Ver D-XXX.\n")
    _decision(tmp_path, ("D-XXX", "segunda", "Segunda"))
    assert script.main(["--root", str(tmp_path)]) == script.EXIT_AMBIGUOUS
    assert (tmp_path / "docs/decisiones/D-002-primera.md").exists()
    assert (tmp_path / "docs/decisiones/D-003-segunda.md").exists()


def test_references_outside_the_diff_do_not_fail_the_run(tmp_path: Path) -> None:
    """El tablero cita decisiones sin mergear: es un aviso informativo, no un error."""
    before, after = _repo_with_base_and_push(
        tmp_path, [("D-001", "uno", "Uno")], [("D-XXX", "nueva", "Nueva")]
    )
    _write(tmp_path, "docs/TABLERO.md", "Otro PR: D-XXX.\n")
    assert script.main(["--root", str(tmp_path), "--before", before, "--after", after]) == 0


def test_added_files_lists_only_the_decisions_added_by_the_push(tmp_path: Path) -> None:
    stale = [("D-001", "uno", "Uno"), ("D-XXX", "vieja", "Vieja")]
    before, after = _repo_with_base_and_push(tmp_path, stale, [("D-XXX", "nueva", "Nueva")])
    assert script.added_files(tmp_path, before, after) == {"D-XXX-nueva.md"}


def test_before_of_zeros_falls_back_to_the_parent_commit(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _setup(tmp_path, ("D-001", "uno", "Uno"))
    _commit(tmp_path, "base")
    spec = _write(tmp_path, "docs/SPEC.md", "x\n")
    after = _commit(tmp_path, "push")
    assert script.changed_files(tmp_path, "0" * 40, after) == [spec]


def test_bad_range_fails_with_a_clear_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _git(tmp_path, "init", "-q")
    _setup(tmp_path, ("D-001", "uno", "Uno"), ("D-XXX", "nueva", "Nueva"))
    assert script.main(["--root", str(tmp_path), "--before", "abc", "--after", "def"]) == 1
    assert "git diff" in capsys.readouterr().err


def test_before_without_after_is_a_usage_error(tmp_path: Path) -> None:
    _setup(tmp_path, ("D-001", "uno", "Uno"))
    with pytest.raises(SystemExit):
        script.main(["--root", str(tmp_path), "--before", "abc"])


# --- check-index: el índice no se edita a mano -------------------------------------------------


def _repo_with_base(root: Path) -> str:
    """Repositorio con D-001 y D-002 y su índice generado; devuelve el commit base."""
    _git(root, "init", "-q")
    _setup(root, ("D-001", "uno", "Uno"), ("D-002", "dos", "Dos"))
    return _commit(root, "base")


def test_check_index_passes_on_a_generated_index(tmp_path: Path) -> None:
    _setup(tmp_path, ("D-001", "uno", "Uno"), ("D-XXX", "nueva", "Nueva"))
    assert script.check_index(tmp_path) == []
    assert script.main(["--root", str(tmp_path), "--check-index"]) == 0


def test_check_index_fails_when_a_row_is_edited_by_hand(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _setup(tmp_path, ("D-001", "uno", "Uno"), ("D-002", "dos", "Dos"))
    path = tmp_path / "docs/decisiones.md"
    path.write_text(path.read_text(encoding="utf-8").replace("| Dos |", "| Dos editado |"), "utf-8")
    assert script.main(["--root", str(tmp_path), "--check-index"]) == 1
    err = capsys.readouterr().err
    assert "Dos editado" in err and "no lo edites a mano" in err


def test_check_index_with_base_ignores_decisions_the_pr_changes(tmp_path: Path) -> None:
    """Un PR cambia el estado de D-001 y añade una D-XXX sin tocar el índice: lo hace la Action."""
    before = _repo_with_base(tmp_path)
    _decision(tmp_path, ("D-001", "uno", "Uno"), state="Sustituida por D-002")
    _decision(tmp_path, ("D-XXX", "nueva", "Nueva"))
    _commit(tmp_path, "pr")
    assert script.check_index(tmp_path, before) == []
    assert script.check_index(tmp_path) != []  # sin base, el índice sí está desfasado


def test_check_index_with_base_fails_on_hand_edit_of_an_untouched_decision(tmp_path: Path) -> None:
    before = _repo_with_base(tmp_path)
    path = tmp_path / "docs/decisiones.md"
    path.write_text(path.read_text(encoding="utf-8").replace("| Dos |", "| Dos editado |"), "utf-8")
    _decision(tmp_path, ("D-001", "uno", "Uno"), state="Descartada")  # D-001 sí lo toca el PR
    _commit(tmp_path, "pr")
    problems = script.check_index(tmp_path, before)
    assert problems and all("Dos" in p for p in problems)


# --- workflows y repositorio real --------------------------------------------------------------


def test_workflow_commits_before_failing_on_ambiguous_references() -> None:
    """El job tiene que commitear lo numerado y fallar después, no abortar antes del commit."""
    text = (ROOT / ".github/workflows/renumber-decisions.yml").read_text(encoding="utf-8")
    assert "continue-on-error: true" in text
    assert "docs/decisiones/**" in text
    assert text.index("Commit y push") < text.index("steps.renumber.outcome == 'failure'")


def test_ci_checks_the_decisions_index_on_pull_requests() -> None:
    text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "--check-index" in text and "pull_request" in text


def test_real_repo_decisions_are_consistent() -> None:
    """Nombres, cabeceras, metadatos y sin IDs repetidos; los D-XXX pendientes son válidos."""
    decisions = script.load_decisions(ROOT)
    assert decisions
    header = (ROOT / "docs/decisiones.md").read_text(encoding="utf-8")
    assert script.INDEX_START in header and script.INDEX_END in header
    numbered = [d for d in decisions if d.numbered]
    ids = [int(d.token[2:]) for d in numbered]
    assert ids == sorted(ids) and max(ids) >= len(set(ids))
