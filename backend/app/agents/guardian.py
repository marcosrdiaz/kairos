"""Guardián determinista (`SPEC.md` §9, diseño del MVP §4.4, D-010).

`check` es una función pura (sin BD ni red). Reglas (detalle en la decisión del guardián T1-16):

1. **Patrones prohibidos** de `prompts/forbidden.yaml`, sobre el texto sin acentos y en minúsculas.
2. **Cifras** (`guardian_figures.py`): cada número casa, en valor absoluto, con alguna evidencia,
   con las tolerancias de ese módulo. Un año fuera de las evidencias y los números en palabras
   mayores que diez son cifras desconocidas.
3. **Forma**: en voz, ≤ 3 frases contando las ya emitidas (`sentence_index`, base 0); en impacto,
   la primera frase (`sentence_index == 0`) lleva una cifra en € (no vale otra moneda).
"""

import re
import unicodedata
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from app.agents import guardian_figures as figs
from app.schemas.agents import (
    GuardianChannel,
    GuardianFigure,
    GuardianReason,
    GuardianRequest,
    GuardianVerdict,
    QuestionKind,
)
from app.schemas.agents import GuardianReasonCode as Code

FORBIDDEN_PATH = Path(__file__).parent / "prompts" / "forbidden.yaml"
MAX_VOICE_SENTENCES = 3

_ABBREVIATIONS = re.compile(r"\b(?:ee\.\s?uu|p\.\s?ej|etc|aprox|sr|sra|dr|p\.\s?b|p\.\s?p)\.")
_SENTENCE_END = re.compile(r"[.!?…]+(?=\s|$)")


@dataclass(frozen=True)
class ForbiddenPattern:
    id: str
    regex: re.Pattern[str]
    blocks: tuple[str, ...]
    allows: tuple[str, ...]


@dataclass(frozen=True)
class ForbiddenConfig:
    patterns: tuple[ForbiddenPattern, ...]
    exempt_names: tuple[re.Pattern[str], ...]


def _normalize_with_map(text: str) -> tuple[str, list[int]]:
    """Texto sin acentos y en minúsculas, y el índice del carácter original de cada carácter."""
    chars: list[str] = []
    origin: list[int] = []
    for index, char in enumerate(text):
        for part in unicodedata.normalize("NFKD", char):
            if unicodedata.combining(part):
                continue
            for lowered in part.lower():
                chars.append(lowered)
                origin.append(index)
    return "".join(chars), origin


def normalize(text: str) -> str:
    return _normalize_with_map(text)[0]


def _original(text: str, origin: list[int], start: int, end: int) -> str:
    return text[origin[start] : origin[end - 1] + 1].strip()


def _as_strings(raw: Any, where: str) -> tuple[str, ...]:
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise ValueError(f"forbidden.yaml: {where} debe ser una lista de textos")
    return tuple(raw)


@cache
def load_config() -> ForbiddenConfig:
    raw = yaml.safe_load(FORBIDDEN_PATH.read_text(encoding="utf-8"))
    placeholders: dict[str, str] = raw.get("placeholders") or {}
    patterns: list[ForbiddenPattern] = []
    for item in raw["patterns"]:
        source = str(item["regex"])
        for name, value in placeholders.items():
            source = source.replace(f"<{name}>", value)
        pattern_id = str(item["id"])
        patterns.append(
            ForbiddenPattern(
                id=pattern_id,
                regex=re.compile(source),
                blocks=_as_strings(item.get("blocks") or [], f"{pattern_id}.blocks"),
                allows=_as_strings(item.get("allows") or [], f"{pattern_id}.allows"),
            )
        )
    exempt = _as_strings(raw.get("figure_exempt_names") or [], "figure_exempt_names")
    return ForbiddenConfig(tuple(patterns), tuple(re.compile(source) for source in exempt))


def find_forbidden(text: str) -> list[tuple[str, str]]:
    """Pares (id del patrón, fragmento original) de los patrones prohibidos que aparecen."""
    normalized, origin = _normalize_with_map(text)
    hits: list[tuple[str, str]] = []
    for pattern in load_config().patterns:
        match = pattern.regex.search(normalized)
        if match is not None:
            start, end = match.span()
            snippet = _original(text, origin, start, end) if end > start else text.strip()
            hits.append((pattern.id, snippet))
    return hits


def extract_figures(normalized: str) -> list[figs.Figure]:
    return figs.extract_figures(normalized, load_config().exempt_names)


def count_sentences(normalized: str) -> int:
    text = _ABBREVIATIONS.sub(lambda m: m.group().replace(".", " "), normalized)
    return sum(1 for part in _SENTENCE_END.split(text) if re.search(r"\w", part))


def _reason(code: Code, detail: str) -> GuardianReason:
    return GuardianReason(code=code, detail=detail)


def check(request: GuardianRequest) -> GuardianVerdict:
    """Valida una frase (o un texto entero, con `sentence_index` 0) contra las reglas."""
    text = request.text
    normalized, origin = _normalize_with_map(text)
    reasons = [
        _reason(Code.FORBIDDEN_PATTERN, f"«{snippet}» parece una orden o recomendación ({pid})")
        for pid, snippet in find_forbidden(text)
    ]

    found = extract_figures(normalized)
    figures: list[GuardianFigure] = []
    has_eur = False
    for figure in found:
        shown = _original(text, origin, figure.start, figure.end)
        match = figs.best_match(figure, request.evidence)
        if match is None:
            reasons.append(_reason(Code.UNKNOWN_FIGURE, f"«{shown}» no está en las herramientas"))
        # "Te ha restado unos 470" también da la cifra en euros si casa con una evidencia en €.
        unitless_eur = figure.unit == "number" and match is not None and figs.is_currency(match)
        has_eur = has_eur or figure.unit == "EUR" or unitless_eur
        calc_id = match.calc_id if match else None
        value, unit = figure.value, figure.unit
        figures.append(GuardianFigure(text=shown, value=value, unit=unit, matched_calc_id=calc_id))

    for start, end in figs.number_words(normalized, found):
        shown = _original(text, origin, start, end)
        detail = f"«{shown}»: las cifras van en dígitos y salen de las herramientas"
        reasons.append(_reason(Code.UNKNOWN_FIGURE, detail))

    index = max(0, request.sentence_index)
    total = index + count_sentences(normalized)
    if request.channel == GuardianChannel.VOICE and total > MAX_VOICE_SENTENCES:
        detail = f"{total} frases en voz; el máximo es {MAX_VOICE_SENTENCES}"
        reasons.append(_reason(Code.TOO_LONG, detail))

    if request.question_kind == QuestionKind.IMPACT and index == 0 and not has_eur:
        detail = "La pregunta es de impacto y la primera frase no da una cifra en euros"
        reasons.append(_reason(Code.MISSING_EUR, detail))

    return GuardianVerdict(ok=not reasons, reasons=reasons, figures=figures)
