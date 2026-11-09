#!/usr/bin/env python3
"""Numera las decisiones provisionales de `docs/decisiones/` y regenera el índice.

Cada decisión es un fichero `docs/decisiones/D-NNN-slug.md`. Las ramas crean los nuevos como
`D-XXX-slug.md` (y `D-XXX-a-slug.md`, `D-XXX-b-slug.md`… si una rama trae varios), con
`### D-XXX · Título` en la primera línea. Al entrar en `main`, este script (lo lanza la Action
`renumber-decisions`) asigna los siguientes IDs correlativos, renombra el fichero (`git mv`), cambia
el ID dentro y en las referencias de los ficheros que ese commit modificó, y regenera el índice de
`docs/decisiones.md` (entre `<!-- INDICE:INICIO -->` y `<!-- INDICE:FIN -->`, no se edita a mano).

Reglas:
- El siguiente ID es el mayor `D-NNN` ya usado, más uno. Se numera primero lo que quedó pendiente de
  pushes anteriores y luego lo que añade este push; dentro de cada grupo, por sufijo (`-a`, `-b`) y
  slug.
- La fecha, el título y el estado del índice se leen de cada fichero (`- Fecha: … Estado: …`).
  El índice solo lista las decisiones ya numeradas: un PR que añade una `D-XXX` no toca
  `decisiones.md`, así que dos PRs no entran en conflicto.
- Una referencia con sufijo (`D-XXX-b`) siempre es inequívoca. Una `D-XXX` sin sufijo en el texto
  solo se sustituye si el push (`--before` y `--after`) añade **un solo** fichero `D-XXX-slug.md`;
  si añade varios o ninguno, se deja y se avisa. Las pendientes de pushes anteriores se numeran,
  pero no hacen ambigua la referencia del push actual. Sin `--before` y `--after` basta con que
  haya un solo fichero `D-XXX-slug.md`.
- Las referencias solo se sustituyen en las decisiones que se numeran y en los ficheros del commit
  que dispara la Action (`git diff --name-only`). Un `D-XXX` en cualquier otro fichero (p. ej. el
  tablero) no se toca: solo se avisa. No se tocan los ficheros `PROTECTED`.
- Una decisión ya numerada nunca se renombra ni se renumera. Si está en el diff del push, sí se
  sustituyen sus referencias `D-XXX` (p. ej. «Estado: Sustituida por D-XXX» de una antigua que va
  en el mismo PR que la nueva); si no está en el diff, no se toca y se avisa como a cualquier otro
  fichero.
- Idempotente: sin `D-XXX` y con el índice al día no cambia nada y sale con 0.
- Códigos de salida: 1 si el estado es inconsistente (nombre o cabecera de un fichero mal formados,
  IDs o sufijos repetidos, marcadores del índice ausentes, `--check-index` con diferencias); no se
  escribe nada. 2 si quedan referencias `D-XXX` ambiguas: antes de salir se escribe todo lo que sí
  se pudo numerar, para que la Action lo commitee, y el job termina en rojo.

Uso: `python scripts/renumber_decisions.py [--root RUTA] [--before SHA --after SHA]`.
`--index-only` solo regenera el índice. `--check-index [--base SHA]` comprueba que el índice
coincide con el generado; con `--base` se ignoran las filas de las decisiones que cambia el PR
(la Action las regenera al entrar en `main`). Solo biblioteca estándar.
"""

import argparse
import fnmatch
import io
import re
import subprocess
import sys
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

DECISIONS = "docs/decisiones.md"
DIR_NAME = "decisiones"
DECISIONS_DIR = f"docs/{DIR_NAME}"
INDEX_START = "<!-- INDICE:INICIO -->"
INDEX_END = "<!-- INDICE:FIN -->"
MAX_FILE_BYTES = 2_000_000
AMBIGUOUS_WARNING = "AVISO: referencias ambiguas a"
EXIT_AMBIGUOUS = 2

# Ficheros que explican la convención `D-XXX`: se dejan tal cual, estén o no en el diff.
PROTECTED = (
    "CLAUDE.md",
    ".claude/commands/*",
    "scripts/renumber_decisions.py",
    "backend/tests/test_renumber_decisions.py",
    ".github/workflows/renumber-decisions.yml",
    DECISIONS,
)
# Las decisiones ya numeradas (`D-NNN-*.md`) no están aquí a propósito: nunca se renombran ni se
# renumeran (`_Plan` solo numera las `D-XXX`), pero sí se sustituyen las referencias `D-XXX` de su
# texto si el fichero está en el diff del push (caso típico: «Estado: Sustituida por D-XXX» en una
# antigua que va en el PR de la nueva).

_TOKEN = r"D-XXX(?:-[a-z])?"
_REF = re.compile(rf"(?<![\w-])({_TOKEN})(?![\w-])")
_NAME = re.compile(r"^(D-(?:\d{3}|XXX(?:-[a-z])?))-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
_HEADING = re.compile(r"^### (D-\d{3}|D-XXX(?:-[a-z])?) · (.+?)\s*$")
_META = re.compile(r"^- Fecha: (\d{4}-\d{2}-\d{2})\b.*\bEstado: ([^·]+?)\s*$")
_ROW_ID = re.compile(r"^\| \[(D-\d{3})\]")


class RenumberError(Exception):
    """Estado inconsistente de `docs/decisiones/` (nombres, IDs repetidos, índice…)."""


@dataclass(frozen=True)
class Decision:
    path: Path
    token: str  # `D-001`, `D-XXX` o `D-XXX-a`
    slug: str
    title: str
    date: str
    state: str
    text: str

    @property
    def numbered(self) -> bool:
        return not self.token.startswith("D-XXX")


def _tracked_files(root: Path) -> list[Path]:
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True
        ).stdout.decode("utf-8")
    except (OSError, subprocess.CalledProcessError):
        skip = {".git", "node_modules", ".venv", "__pycache__"}
        return [
            p
            for p in root.rglob("*")
            if p.is_file() and not skip.intersection(p.relative_to(root).parts)
        ]
    return [root / name for name in out.split("\0") if name]


def _git_diff(root: Path, before: str, after: str, *args: str, paths: Iterable[str] = ()) -> str:
    """Salida de `git diff` entre `before` y `after`, limitada a `paths` si se indican.

    Un `before` de ceros (rama nueva) se sustituye por el padre de `after`.
    """
    if not before.strip("0"):
        before = f"{after}^"
    try:
        return subprocess.run(
            ["git", "diff", *args, f"{before}..{after}", *(["--", *paths] if paths else [])],
            cwd=root,
            check=True,
            capture_output=True,
        ).stdout.decode("utf-8")
    except (OSError, subprocess.CalledProcessError) as error:
        raise RenumberError(f"No se puede calcular git diff {before}..{after}: {error}") from error


def changed_files(root: Path, before: str, after: str) -> list[Path]:
    """Ficheros que cambió el rango `before..after` (los del push que dispara la Action)."""
    out = _git_diff(root, before, after, "--name-only", "-z", "--diff-filter=d")
    return [root / name for name in out.split("\0") if name]


def added_files(root: Path, before: str, after: str) -> set[str]:
    """Nombres de los ficheros de `docs/decisiones/` que añade el rango `before..after`."""
    out = _git_diff(
        root, before, after, "--name-only", "-z", "--diff-filter=A", paths=[DECISIONS_DIR]
    )
    return {Path(name).name for name in out.split("\0") if name}


def _is_protected(rel: str) -> bool:
    return any(fnmatch.fnmatch(rel, pattern) for pattern in PROTECTED)


def _read_text(path: Path) -> str | None:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return None
        return path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _write_text(path: Path, text: str) -> None:
    path.write_bytes(text.encode("utf-8"))


def load_decisions(root: Path) -> list[Decision]:
    """Lee y valida todos los ficheros de `docs/decisiones/`, ordenados por nombre."""
    directory = root / DECISIONS_DIR
    found: list[Decision] = []
    for path in sorted(directory.glob("D-*.md")) if directory.is_dir() else []:
        name = _NAME.match(path.name)
        if not name:
            raise RenumberError(
                f"{path.name}: el nombre debe ser D-NNN-slug.md o D-XXX[-a]-slug.md "
                "(slug en minúsculas, sin tildes ni espacios)"
            )
        text = _read_text(path)
        if text is None:
            raise RenumberError(f"No se puede leer {path.name}")
        lines = text.splitlines()
        head = _HEADING.match(lines[0]) if lines else None
        if not head or head.group(1) != name.group(1):
            raise RenumberError(f"{path.name}: la primera línea debe ser «### {name.group(1)} · …»")
        meta = next((m for line in lines[1:6] if (m := _META.match(line))), None)
        if not meta:
            raise RenumberError(f"{path.name}: falta «- Fecha: AAAA-MM-DD … Estado: …»")
        found.append(
            Decision(path, name.group(1), name.group(2), head.group(2), *meta.groups(), text)
        )
    for what, tokens in (
        ("IDs repetidos entre ficheros", [d.token for d in found if d.numbered]),
        ("Sufijos repetidos", [d.token for d in found if d.token != "D-XXX" and not d.numbered]),
    ):
        repeated = sorted(t for t, n in Counter(tokens).items() if n > 1)
        if repeated:
            raise RenumberError(f"{what}: {', '.join(repeated)}")
    return found


def render_index(decisions: Iterable[Decision]) -> list[str]:
    rows = [
        f"| [{d.token}]({DIR_NAME}/{d.path.name}) | {d.date} | {d.title} | {d.state} |"
        for d in sorted(decisions, key=lambda d: d.token)
        if d.numbered
    ]
    return ["| ID | Fecha | Título | Estado |", "| --- | --- | --- | --- |", *rows]


def _split_index(root: Path) -> tuple[str, list[str], str]:
    text = _read_text(root / DECISIONS)
    if text is None or INDEX_START not in text or INDEX_END not in text:
        raise RenumberError(f"Faltan los marcadores {INDEX_START} / {INDEX_END} en {DECISIONS}")
    before, _, rest = text.partition(INDEX_START)
    block, _, after = rest.partition(INDEX_END)
    return before, [line for line in block.splitlines() if line.strip()], after


def write_index(root: Path) -> bool:
    """Regenera el índice de `decisiones.md`. Devuelve `True` si cambió."""
    before, current, after = _split_index(root)
    table = render_index(load_decisions(root))
    if current == table:
        return False
    body = "\n" + "\n".join(table) + "\n"
    _write_text(root / DECISIONS, before + INDEX_START + body + INDEX_END + after)
    return True


def check_index(root: Path, base: str | None = None) -> list[str]:
    """Diferencias entre el índice de `decisiones.md` y el que salen de los ficheros.

    Con `base` se ignoran las filas de las decisiones que cambian entre `base` y `HEAD`: un PR no
    regenera el índice, lo hace la Action al entrar en `main`.
    """
    _, current, _ = _split_index(root)
    expected = render_index(load_decisions(root))
    if base:
        names = _git_diff(root, base, "HEAD", "--name-only", "-z", paths=[DECISIONS_DIR])
        touched = {
            f"D-{m.group(1)}"
            for n in names.split("\0")
            if n and (m := re.match(r"D-(\d{3})-", Path(n).name))
        }

        def untouched(lines: list[str]) -> list[str]:
            return [x for x in lines if not ((m := _ROW_ID.match(x)) and m.group(1) in touched)]

        current, expected = untouched(current), untouched(expected)
    return [f"sobra o difiere: {x}" for x in current if x not in expected] + [
        f"falta o difiere: {x}" for x in expected if x not in current
    ]


class _Plan:
    """ID asignado a cada decisión pendiente y a qué ID apunta una `D-XXX` sin sufijo."""

    def __init__(self, decisions: list[Decision], added: set[str] | None) -> None:
        pending = [d for d in decisions if not d.numbered]
        pending.sort(key=lambda d: (added is not None and d.path.name in added, d.token, d.slug))
        nxt = max((int(d.token[2:]) for d in decisions if d.numbered), default=0) + 1
        self.order = pending
        self.ids = {d.path: f"D-{nxt + i:03d}" for i, d in enumerate(pending)}
        self._by_token = {d.token: self.ids[d.path] for d in pending}
        fresh = [
            d for d in pending if d.token == "D-XXX" and (added is None or d.path.name in added)
        ]
        self._bare = self.ids[fresh[0].path] if len(fresh) == 1 else None

    def ref(self, token: str) -> str | None:
        """ID de una referencia, o `None` si es ambigua."""
        return self._bare if token == "D-XXX" else self._by_token.get(token)


def _sub_refs(text: str, plan: _Plan, ambiguous: list[str]) -> str:
    def replace(m: re.Match[str]) -> str:
        new = plan.ref(m.group(1))
        if new is None:
            ambiguous.append(m.group(1))
            return m.group(0)
        return new

    return _REF.sub(replace, text)


def _move(root: Path, src: Path, dst: Path) -> None:
    try:
        subprocess.run(["git", "mv", str(src), str(dst)], cwd=root, check=True, capture_output=True)
    except (OSError, subprocess.CalledProcessError):
        src.rename(dst)


def renumber(
    root: Path, files: Iterable[Path] | None = None, added: set[str] | None = None
) -> list[str]:
    """Numera, regenera el índice y devuelve un informe. Vacío si no había nada que hacer.

    `files` son los ficheros (además de las decisiones que se numeran) donde se sustituyen las
    referencias: los que cambió el commit que dispara la Action. `added` son los nombres de los
    ficheros de decisión que añade ese commit (ver `added_files`).
    """
    decisions = load_decisions(root)
    _split_index(root)  # falla antes de escribir nada si faltan los marcadores
    plan = _Plan(decisions, added)
    ambiguous: list[str] = []
    report: list[str] = []
    for d in plan.order:
        new_id = plan.ids[d.path]
        first, sep, rest = d.text.partition("\n")
        text = re.sub(rf"^### {_TOKEN}", f"### {new_id}", first) + sep
        _move(root, d.path, d.path.with_name(f"{new_id}-{d.slug}.md"))
        _write_text(
            d.path.with_name(f"{new_id}-{d.slug}.md"), text + _sub_refs(rest, plan, ambiguous)
        )
        report.append(f"{d.token} → {new_id}  {d.title}")
    if plan.order:
        report += _other_files(root, files or [], plan, ambiguous)
    if write_index(root):
        report.append("Índice de decisiones regenerado")
    for token in sorted(set(ambiguous)):
        report.append(f"{AMBIGUOUS_WARNING} {token} (no hay una única D-XXX nueva)")
    return report


def _other_files(root: Path, files: Iterable[Path], plan: _Plan, ambiguous: list[str]) -> list[str]:
    report: list[str] = []
    processed: set[str] = set()
    for path in files:
        rel = path.relative_to(root).as_posix()
        processed.add(rel)
        original = None if _is_protected(rel) else _read_text(path)
        if original is None or "D-XXX" not in original:
            continue
        updated = _sub_refs(original, plan, ambiguous)
        if updated != original:
            _write_text(path, updated)
            report.append(f"  referencias actualizadas en {rel}")
    for path in _tracked_files(root):
        rel = path.relative_to(root).as_posix()
        if rel in processed or _is_protected(rel):
            continue
        other = _read_text(path)
        if other is not None and _REF.search(other):
            report.append(f"AVISO: {rel} cita D-XXX pero no está en el diff; no se toca")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0] if __doc__ else None)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--before", help="commit anterior al push (github.event.before)")
    parser.add_argument("--after", help="commit del push (github.sha)")
    parser.add_argument("--index-only", action="store_true", help="solo regenera el índice")
    parser.add_argument("--check-index", action="store_true", help="comprueba el índice y sale")
    parser.add_argument("--base", help="con --check-index: commit base del PR")
    args = parser.parse_args(argv)
    if bool(args.before) != bool(args.after):
        parser.error("--before y --after van juntos")
    for stream in (sys.stdout, sys.stderr):  # consolas de Windows sin UTF-8
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
    try:
        if args.check_index:
            problems = check_index(args.root, args.base)
            if problems:
                print("\n".join(problems), file=sys.stderr)
                print(
                    "ERROR: el índice de docs/decisiones.md no coincide con los ficheros. "
                    "Se genera solo (scripts/renumber_decisions.py --index-only): "
                    "no lo edites a mano.",
                    file=sys.stderr,
                )
                return 1
            print("El índice de decisiones está al día.")
            return 0
        if args.index_only:
            print("Índice regenerado." if write_index(args.root) else "El índice ya estaba al día.")
            return 0
        files = changed_files(args.root, args.before, args.after) if args.before else []
        added = added_files(args.root, args.before, args.after) if args.before else None
        report = renumber(args.root, files, added)
    except RenumberError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("\n".join(report) if report else "Nada que renumerar.")
    if any(line.startswith(AMBIGUOUS_WARNING) for line in report):
        print(
            "ERROR: quedan referencias D-XXX sin numerar; lo demás ya está numerado. "
            "Corrígelas a mano con el ID de la decisión.",
            file=sys.stderr,
        )
        return EXIT_AMBIGUOUS
    return 0


if __name__ == "__main__":
    sys.exit(main())
