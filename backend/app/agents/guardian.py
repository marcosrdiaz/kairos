"""Guardián determinista (`SPEC.md` §9, diseño del MVP §4.4, D-010).

`check` es una función pura (sin BD ni red). Reglas (detalle en la decisión del guardián T1-16):

1. **Patrones prohibidos** de `prompts/forbidden.yaml`, sobre el texto sin acentos y en minúsculas.
2. **Cifras**: cada número casa, en valor absoluto, con alguna evidencia. `GuardianFigure.unit`:
   `EUR`, `percent`, `pp` ("puntos"), `bp` (puntos básicos) o `number` (sin unidad). Tolerancia:
   € → el mayor de 1 € y 0,5 %; %/pp → 0,5 pp; pb → 0,5 pb; y siempre el redondeo de lo escrito
   ("42 mil euros" casa con 42.380). No son cifras los enteros sin unidad de 0 a 10, los días del
   mes, las horas ni los nombres de `figure_exempt_names` ("S&P 500"). Un año fuera de las
   evidencias y los números en palabras mayores que diez son cifras desconocidas.
3. **Forma**: en voz, ≤ 3 frases contando las ya emitidas (`sentence_index`, base 0); en impacto,
   la primera frase (`sentence_index == 0`) lleva una cifra en €.

Extensión: el chequeo con modelo (`GUARDIAN_LLM_CHECK`, D-010) va en quien llama, tras un `ok`.
"""

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal
from functools import cache
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from app.schemas.agents import (
    Evidence,
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

_EUR_TOL = Decimal(1)
_EUR_REL_TOL = Decimal("0.005")
_PP_TOL = Decimal("0.5")
_BP_TOL = Decimal("0.005")  # 0,5 pb expresado en pp
_HUNDRED = Decimal(100)

_NUMBER = re.compile(
    r"(?<![\w.,])(?P<sign>[-+−–]\s?)?"
    r"(?P<num>\d{1,3}(?:\.\d{3})+(?:,\d+)?(?!\d)|\d+(?:[.,]\d+)?)(?![\d\w])"
    r"(?:\s+(?P<mult>mil\s+millones|millones|millon|mil)\b)?"
    r"(?:\s*(?:de\s+)?(?P<unit>€|euros?\b|eur\b|%|por\s+ciento\b|por\s+cien\b"
    r"|puntos?\s+basicos\b|pb\b|p\.\s?b\.|puntos?\s+porcentuales\b|pp\b|p\.\s?p\.|puntos?\b))?"
)
_GROUPED = re.compile(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?")
_MULTIPLIERS = {"mil": 10**3, "millon": 10**6, "millones": 10**6, "mil millones": 10**9}
_DAY_OF_MONTH = re.compile(
    r"\b\d{1,2}(?=\s+de\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre"
    r"|setiembre|octubre|noviembre|diciembre)\b)"
)
_TIME_OF_DAY = re.compile(r"\b\d{1,2}:\d{2}\b")
_NUMBER_WORDS = re.compile(
    r"\b(?:once|doce|trece|catorce|quince|dieci[a-z]+|veinte|veinti[a-z]+|treinta|cuarenta"
    r"|cincuenta|sesenta|setenta|ochenta|noventa|cien|ciento|(?:doscient|trescient|cuatrocient"
    r"|quinient|seiscient|setecient|ochocient|novecient)(?:os|as)|mil|millon(?:es)?"
    r"|millardos?|billon(?:es)?)\b"
)
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


@dataclass(frozen=True)
class _Figure:
    start: int
    end: int
    value: Decimal
    unit: str
    step: Decimal  # medio paso del último dígito escrito, ya multiplicado


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


# --- Cifras ---


def _mask(normalized: str, spans: list[tuple[int, int]]) -> str:
    chars = list(normalized)
    for start, end in spans:
        chars[start:end] = " " * (end - start)
    return "".join(chars)


def _unit(token: str | None) -> str:
    if token is None:
        return "number"
    if token[0] in "€e":
        return "EUR"
    if token[0] in "%" or token.startswith("por"):
        return "percent"
    if token.startswith("pb") or (token.startswith("p.") and "b" in token) or "basico" in token:
        return "bp"
    return "pp"


def _parse(match: re.Match[str]) -> tuple[Decimal, Decimal]:
    """Valor y medio paso del último dígito, sin multiplicar."""
    num = match["num"]
    if _GROUPED.fullmatch(num):
        num = num.replace(".", "")
    num = num.replace(",", ".")
    decimals = len(num.split(".")[1]) if "." in num else 0
    sign = -1 if match["sign"] and match["sign"].strip() in "-−–" else 1
    return Decimal(num) * sign, Decimal(5) * Decimal(10) ** -(decimals + 1)


def extract_figures(normalized: str) -> list[_Figure]:
    spans = [m.span() for m in _DAY_OF_MONTH.finditer(normalized)]
    spans.extend(m.span() for m in _TIME_OF_DAY.finditer(normalized))
    for exempt in load_config().exempt_names:
        spans.extend(m.span() for m in exempt.finditer(normalized))
    figures: list[_Figure] = []
    for match in _NUMBER.finditer(_mask(normalized, spans)):
        value, step = _parse(match)
        mult = Decimal(_MULTIPLIERS[" ".join(match["mult"].split())] if match["mult"] else 1)
        unit = _unit(match["unit"])
        small = unit == "number" and mult == 1 and step == Decimal("0.5") and abs(value) <= 10
        if not small:
            figures.append(_Figure(*match.span(), value * mult, unit, step * mult))
    return figures


def _is_eur(evidence: Evidence) -> bool:
    return evidence.unit.upper() in {"EUR", "€"}


def _evidence_pp(evidence: Evidence) -> Decimal | None:
    """La evidencia en puntos porcentuales, si es un porcentaje."""
    unit = evidence.unit.lower()
    if unit == "fraction":
        return abs(evidence.value) * _HUNDRED
    if unit in {"percent", "pct", "%", "pp"}:
        return abs(evidence.value)
    if unit in {"bp", "pb"}:
        return abs(evidence.value) / _HUNDRED
    return None


def _distance(figure: _Figure, evidence: Evidence) -> Decimal | None:
    """Distancia relativa a la tolerancia (≤ 1 casa) o `None` si no son comparables o no casan."""
    value = abs(figure.value)
    candidates: list[tuple[Decimal, Decimal, Decimal]] = []  # (texto, evidencia, tolerancia)
    pp = _evidence_pp(evidence)
    if figure.unit in {"EUR", "number"} and _is_eur(evidence):
        target = abs(evidence.value)
        candidates.append((value, target, max(_EUR_TOL, target * _EUR_REL_TOL, figure.step)))
    if figure.unit in {"percent", "pp", "number"} and pp is not None:
        candidates.append((value, pp, max(_PP_TOL, figure.step)))
    if figure.unit == "bp" and pp is not None:
        candidates.append((value / _HUNDRED, pp, max(_BP_TOL, figure.step / _HUNDRED)))
    if figure.unit == "number":
        candidates.append((value, abs(evidence.value), figure.step))
    distances = [abs(text - target) / tol for text, target, tol in candidates if tol > 0]
    matching = [d for d in distances if d <= 1]
    return min(matching) if matching else None


def _best_match(figure: _Figure, evidence: list[Evidence]) -> Evidence | None:
    """La evidencia más cercana; a igualdad, la que tiene `calc_id`."""
    distances = [_distance(figure, item) for item in evidence]
    scored = [(d, evidence[i].calc_id is None, i) for i, d in enumerate(distances) if d is not None]
    return evidence[min(scored)[2]] if scored else None


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
        match = _best_match(figure, request.evidence)
        if match is None:
            reasons.append(_reason(Code.UNKNOWN_FIGURE, f"«{shown}» no está en las herramientas"))
        # "Te ha restado unos 470" también da la cifra en euros si casa con una evidencia en €.
        has_eur = has_eur or figure.unit == "EUR" or (match is not None and _is_eur(match))
        calc_id = match.calc_id if match else None
        value, unit = figure.value, figure.unit
        figures.append(GuardianFigure(text=shown, value=value, unit=unit, matched_calc_id=calc_id))

    for word in _NUMBER_WORDS.finditer(_mask(normalized, [(f.start, f.end) for f in found])):
        shown = _original(text, origin, *word.span())
        detail = f"«{shown}»: las cifras van en dígitos y salen de las herramientas"
        reasons.append(_reason(Code.UNKNOWN_FIGURE, detail))

    total = request.sentence_index + count_sentences(normalized)
    if request.channel == GuardianChannel.VOICE and total > MAX_VOICE_SENTENCES:
        detail = f"{total} frases en voz; el máximo es {MAX_VOICE_SENTENCES}"
        reasons.append(_reason(Code.TOO_LONG, detail))

    if request.question_kind == QuestionKind.IMPACT and request.sentence_index == 0 and not has_eur:
        detail = "La pregunta es de impacto y la primera frase no da una cifra en euros"
        reasons.append(_reason(Code.MISSING_EUR, detail))

    return GuardianVerdict(ok=not reasons, reasons=reasons, figures=figures)
