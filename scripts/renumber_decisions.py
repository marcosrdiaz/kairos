#!/usr/bin/env python3
"""Numera las decisiones provisionales de `docs/decisiones.md`.

Las ramas escriben las decisiones nuevas con `D-XXX` (y `D-XXX-a`, `D-XXX-b`… si hay varias en la
misma rama). Al entrar en `main`, este script (lo lanza la Action `renumber-decisions`) asigna los
siguientes IDs correlativos `D-NNN` y los sustituye en la entrada, en la fila del índice y en las
referencias de los ficheros que ese mismo commit ha modificado.

Reglas:
- El siguiente ID es el mayor `D-NNN` ya usado en entradas e índice, más uno.
- Se numera por orden de aparición de las entradas (`### D-XXX · …`). Los sufijos de una misma rama
  mantienen su orden. Varias `D-XXX` sin sufijo (de ramas distintas) se emparejan con su fila del
  índice por orden.
- Una referencia con sufijo (`D-XXX-b`) siempre es inequívoca. Una `D-XXX` sin sufijo en el texto
  solo se sustituye si el push que dispara la Action (`--before` y `--after`) añade **una sola**
  entrada `D-XXX`; si añade varias o ninguna, se deja y se avisa. Las `D-XXX` que `decisiones.md`
  arrastra de pushes anteriores sin numerar (p. ej. porque su Action no llegó a correr) no cuentan:
  se numeran igual, pero no hacen ambigua la referencia del push actual. Sin `--before` y
  `--after` no se sabe qué entradas son nuevas y basta con que haya una sola en el fichero.
- Las referencias solo se sustituyen en `docs/decisiones.md` y en los ficheros del commit que
  dispara la Action (`--before` y `--after`, lo que da `git diff --name-only`). Un `D-XXX` en
  cualquier otro fichero (p. ej. el tablero, que cita decisiones de PRs aún sin mergear) no se toca:
  pertenece a otra decisión pendiente y numerarlo ahora lo apuntaría a la equivocada. Solo se avisa.
  Fuera del propio PR, las decisiones sin mergear se citan por título, no como `D-XXX`.
- No se tocan los textos que explican la convención: la cabecera de `docs/decisiones.md` (antes de
  `## Índice`) y los ficheros de `PROTECTED`.
- Idempotente: sin `D-XXX` no cambia nada y sale con 0. Sale con 1 si hay IDs repetidos o una
  entrada sin fila de índice (o al revés).

Uso: `python scripts/renumber_decisions.py [--root RUTA] [--before SHA --after SHA]`. Sin `--before` y
`--after` solo se procesa `docs/decisiones.md`. Solo biblioteca estándar.
"""

import argparse
import fnmatch
import io
import re
import subprocess
import sys
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

DECISIONS = "docs/decisiones.md"
INDEX_MARKER = "## Índice"
MAX_FILE_BYTES = 2_000_000

# Ficheros que explican la convención `D-XXX`: se dejan tal cual.
PROTECTED = (
    "CLAUDE.md",
    ".claude/commands/*",
    "scripts/renumber_decisions.py",
    "backend/tests/test_renumber_decisions.py",
    ".github/workflows/renumber-decisions.yml",
)

_TOKEN = r"D-XXX(?:-[a-z])?"
_REF = re.compile(rf"(?<![\w-])({_TOKEN})(?![\w-])")
_HEADING = re.compile(rf"^### ({_TOKEN}|D-\d{{3}})(?=\s)")
_ROW = re.compile(rf"^\| ({_TOKEN}|D-\d{{3}}) \|")
_NUMBER = re.compile(r"^D-(\d{3})$")


class RenumberError(Exception):
    """Estado inconsistente de `decisiones.md` (IDs repetidos, entrada sin fila de índice…)."""


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


def added_headings(root: Path, before: str, after: str) -> set[str]:
    """Líneas `### D-XXX…` que añade el rango `before..after` a `docs/decisiones.md`."""
    out = _git_diff(root, before, after, "-U0", paths=[DECISIONS])
    added = (line[1:].rstrip() for line in out.splitlines() if line.startswith("+###"))
    return {
        line for line in added if (m := _HEADING.match(line)) and m.group(1).startswith("D-XXX")
    }


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


class _Plan:
    """IDs asignados a cada `D-XXX` de las entradas, por orden de aparición."""

    def __init__(self, lines: list[str], start: int, added: set[str] | None = None) -> None:
        headings: list[str] = []
        rows: list[str] = []
        numbered_headings: list[str] = []
        numbered_rows: list[str] = []
        fresh: list[int] = []  # posición (entre las `D-XXX` sin sufijo) de las que añade el push
        for line in lines[start:]:
            if m := _HEADING.match(line):
                (headings if m.group(1).startswith("D-XXX") else numbered_headings).append(
                    m.group(1)
                )
                if m.group(1) == "D-XXX" and added is not None and line.rstrip() in added:
                    fresh.append(Counter(headings)["D-XXX"] - 1)
            if m := _ROW.match(line):
                (rows if m.group(1).startswith("D-XXX") else numbered_rows).append(m.group(1))
        self.headings = headings
        self._check(numbered_headings, numbered_rows, headings, rows)
        used = [
            int(n.group(1)) for t in numbered_headings + numbered_rows if (n := _NUMBER.match(t))
        ]
        nxt = max(used, default=0) + 1
        self.ids: dict[tuple[str, int], str] = {}
        seen: Counter[str] = Counter()
        for token in headings:
            self.ids[(token, seen[token])] = f"D-{nxt:03d}"
            seen[token] += 1
            nxt += 1
        # Con `added` (modo Action) la `D-XXX` sin sufijo de una referencia es la única que añade
        # este push; sin él, la única que hay en el fichero.
        self.bare = Counter(headings)["D-XXX"] if added is None else len(fresh)
        self._bare_id = (
            self.ids.get(("D-XXX", fresh[0] if added is not None and fresh else 0))
            if self.bare == 1
            else None
        )

    @staticmethod
    def _check(
        numbered_headings: list[str],
        numbered_rows: list[str],
        headings: list[str],
        rows: list[str],
    ) -> None:
        for what, ids in (("entradas", numbered_headings), ("filas del índice", numbered_rows)):
            repeated = sorted(i for i, n in Counter(ids).items() if n > 1)
            if repeated:
                raise RenumberError(f"IDs repetidos en {what}: {', '.join(repeated)}")
        for what, ids in (("entradas", headings), ("filas del índice", rows)):
            repeated = sorted(i for i, n in Counter(ids).items() if n > 1 and i != "D-XXX")
            if repeated:
                raise RenumberError(f"Sufijos repetidos en {what}: {', '.join(repeated)}")
        if Counter(headings) != Counter(rows):
            raise RenumberError(
                f"Las entradas {sorted(headings)} y las filas del índice {sorted(rows)} no cuadran"
            )

    def ref(self, token: str) -> str | None:
        """ID de una referencia, o `None` si es ambigua."""
        if token == "D-XXX":
            return self._bare_id
        return self.ids.get((token, 0))


def _sub_refs(text: str, plan: _Plan, ambiguous: list[str]) -> str:
    def replace(m: re.Match[str]) -> str:
        new = plan.ref(m.group(1))
        if new is None:
            ambiguous.append(m.group(1))
            return m.group(0)
        return new

    return _REF.sub(replace, text)


def renumber(
    root: Path, files: Iterable[Path] | None = None, added: set[str] | None = None
) -> list[str]:
    """Renumera y devuelve un informe (una línea por ID asignado). Vacío si no había nada.

    `files` son los ficheros (además de `docs/decisiones.md`) donde se sustituyen las referencias:
    los que cambió el commit que dispara la Action. Los demás ficheros con `D-XXX` no se tocan.
    `added` son las líneas `### D-XXX…` que añade ese commit (ver `added_headings`); decide a cuál
    se refiere una `D-XXX` sin sufijo.
    """
    decisions_path = root / DECISIONS
    text = _read_text(decisions_path)
    if text is None:
        raise RenumberError(f"No se puede leer {DECISIONS}")
    lines = text.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if line.startswith(INDEX_MARKER)), 0)
    plan = _Plan(lines, start, added)  # también valida IDs repetidos aunque no haya D-XXX
    if not plan.headings:
        return []

    ambiguous: list[str] = []
    seen_heading: Counter[str] = Counter()
    seen_row: Counter[str] = Counter()
    report: list[str] = []
    out = lines[:start]
    for line in lines[start:]:
        new_line = line
        for pattern, seen in ((_HEADING, seen_heading), (_ROW, seen_row)):
            m = pattern.match(line)
            if m and m.group(1).startswith("D-XXX"):
                token = m.group(1)
                new_id = plan.ids[(token, seen[token])]
                seen[token] += 1
                rest = _sub_refs(line[m.end(1) :], plan, ambiguous)
                new_line = line[: m.start(1)] + new_id + rest
                if pattern is _HEADING:
                    title = line[m.end(1) :].lstrip(" ·").strip()
                    report.append(f"{token} → {new_id}  {title}")
                break
        else:
            new_line = _sub_refs(line, plan, ambiguous)
        out.append(new_line)
    _write_text(decisions_path, "".join(out))

    processed: set[str] = set()
    for path in files or []:
        rel = path.relative_to(root).as_posix()
        processed.add(rel)
        if rel == DECISIONS or _is_protected(rel):
            continue
        original = _read_text(path)
        if original is None or "D-XXX" not in original:
            continue
        updated = _sub_refs(original, plan, ambiguous)
        if updated != original:
            _write_text(path, updated)
            report.append(f"  referencias actualizadas en {rel}")
    for path in _tracked_files(root):
        rel = path.relative_to(root).as_posix()
        if rel == DECISIONS or rel in processed or _is_protected(rel):
            continue
        other = _read_text(path)
        if other is not None and _REF.search(other):
            report.append(f"AVISO: {rel} cita D-XXX pero no está en el diff; no se toca")
    for token in sorted(set(ambiguous)):
        report.append(f"AVISO: referencias ambiguas a {token} (no hay una única D-XXX nueva)")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0] if __doc__ else None)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--before", help="commit anterior al push (github.event.before)")
    parser.add_argument("--after", help="commit del push (github.sha)")
    args = parser.parse_args(argv)
    if bool(args.before) != bool(args.after):
        parser.error("--before y --after van juntos")
    for stream in (sys.stdout, sys.stderr):  # consolas de Windows sin UTF-8
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
    try:
        files = changed_files(args.root, args.before, args.after) if args.before else []
        added = added_headings(args.root, args.before, args.after) if args.before else None
        report = renumber(args.root, files, added)
    except RenumberError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("\n".join(report) if report else "Nada que renumerar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
