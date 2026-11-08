#!/usr/bin/env python3
"""Numera las decisiones provisionales de `docs/decisiones.md`.

Las ramas escriben las decisiones nuevas con `D-XXX` (y `D-XXX-a`, `D-XXX-b`… si hay varias en la
misma rama). Al entrar en `main`, este script (lo lanza la Action `renumber-decisions`) asigna los
siguientes IDs correlativos `D-NNN` y los sustituye en la entrada, en la fila del índice y en las
referencias de los ficheros de texto versionados.

Reglas:
- El siguiente ID es el mayor `D-NNN` ya usado en entradas e índice, más uno.
- Se numera por orden de aparición de las entradas (`### D-XXX · …`). Los sufijos de una misma rama
  mantienen su orden. Varias `D-XXX` sin sufijo (de ramas distintas) se emparejan con su fila del
  índice por orden.
- Una referencia con sufijo (`D-XXX-b`) siempre es inequívoca. Una `D-XXX` sin sufijo en el texto
  solo se sustituye si ese día hay una sola; si hay varias, se deja y se avisa.
- No se tocan los textos que explican la convención: la cabecera de `docs/decisiones.md` (antes de
  `## Índice`) y los ficheros de `PROTECTED`.
- Idempotente: sin `D-XXX` no cambia nada y sale con 0. Sale con 1 si hay IDs repetidos o una
  entrada sin fila de índice (o al revés).

Uso: `python scripts/renumber_decisions.py [--root RUTA]`. Solo biblioteca estándar.
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

    def __init__(self, lines: list[str], start: int) -> None:
        headings: list[str] = []
        rows: list[str] = []
        numbered_headings: list[str] = []
        numbered_rows: list[str] = []
        for line in lines[start:]:
            if m := _HEADING.match(line):
                (headings if m.group(1).startswith("D-XXX") else numbered_headings).append(
                    m.group(1)
                )
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
        self.bare = Counter(headings)["D-XXX"]

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
        if token == "D-XXX" and self.bare > 1:
            return None
        return self.ids.get((token, 0))


def _sub_refs(text: str, plan: _Plan, ambiguous: list[str]) -> str:
    def replace(m: re.Match[str]) -> str:
        new = plan.ref(m.group(1))
        if new is None:
            ambiguous.append(m.group(1))
            return m.group(0)
        return new

    return _REF.sub(replace, text)


def renumber(root: Path, files: Iterable[Path] | None = None) -> list[str]:
    """Renumera y devuelve un informe (una línea por ID asignado). Vacío si no había nada."""
    decisions_path = root / DECISIONS
    text = _read_text(decisions_path)
    if text is None:
        raise RenumberError(f"No se puede leer {DECISIONS}")
    lines = text.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if line.startswith(INDEX_MARKER)), 0)
    plan = _Plan(lines, start)  # también valida IDs repetidos aunque no haya D-XXX
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

    for path in files if files is not None else _tracked_files(root):
        rel = path.relative_to(root).as_posix()
        if rel == DECISIONS or _is_protected(rel):
            continue
        original = _read_text(path)
        if original is None or "D-XXX" not in original:
            continue
        updated = _sub_refs(original, plan, ambiguous)
        if updated != original:
            _write_text(path, updated)
            report.append(f"  referencias actualizadas en {rel}")
    for token in sorted(set(ambiguous)):
        report.append(f"AVISO: quedan referencias ambiguas a {token} (hay varias D-XXX); revísalas")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0] if __doc__ else None)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):  # consolas de Windows sin UTF-8
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
    try:
        report = renumber(args.root)
    except RenumberError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("\n".join(report) if report else "Nada que renumerar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
