"""Extracción y casado de cifras del guardián (`guardian.py`). Funciones puras sobre texto ya
normalizado (sin acentos y en minúsculas).

Unidades de una cifra: `EUR`, `USD`, `GBP`, `percent`, `pp` ("puntos"), `bp` (puntos básicos) o
`number` (sin unidad). El valor es el escrito, con signo y multiplicador ("5M€" = 5.000.000).
Tolerancias (en valor absoluto, siempre al menos el redondeo de lo escrito, "medio paso"):
- € y otras monedas: el mayor de 1 y 0,5 % de la evidencia.
- % y pp: el menor de 0,5 pp y el 10 % de la evidencia (desviación de SPEC §9, ver decisión).
- pb: el menor de 0,5 pb y el 10 % de la evidencia.
- sin unidad: solo el redondeo de lo escrito.
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from app.schemas.agents import Evidence

_EUR_TOL = Decimal(1)
_MONEY_REL_TOL = Decimal("0.005")
_PP_TOL = Decimal("0.5")
_BP_TOL = Decimal("0.005")  # 0,5 pb expresado en pp
_PCT_REL_TOL = Decimal("0.1")
_HUNDRED = Decimal(100)
_CURRENCIES = {"EUR": {"EUR", "€"}, "USD": {"USD", "$"}, "GBP": {"GBP", "£"}}
_UNITLESS = {"", "NUMBER"}

_NUMBER = re.compile(
    r"(?<![\d.,])(?:(?P<pre>€|\$|£|\beur\b|\busd\b|\bgbp\b)\s?)?(?P<sign>[-+−–]\s?)?"
    r"(?P<num>\d{1,3}(?:\.\d{3})+(?:,\d+)?(?!\d)|\d{1,3}(?: \d{3})+(?:,\d+)?(?!\d)"
    r"|\d+(?:[.,]\d+)?)"
    r"(?:\s?(?P<k>k|mm|m)(?![a-z])|\s+(?P<mult>mil\s+millones|millones|millon|mil)\b)?"
    r"(?:(?P<glued>e)\b|\s*(?:de\s+)?(?P<unit>€|euros?\b|eur\b|\$|dolar(?:es)?\b|usd\b|£"
    r"|libras?\b|gbp\b|%|por\s+ciento\b|por\s+cien\b|puntos?\s+basicos\b|pb\b|p\.\s?b\."
    r"|puntos?\s+porcentuales\b|pp\b|p\.\s?p\.|puntos?\b))?"
)
_GROUPED = re.compile(r"\d{1,3}(?:[. ]\d{3})+(?:,\d+)?")
_MULTIPLIERS = {
    "k": 10**3, "mil": 10**3, "m": 10**6, "mm": 10**6, "millon": 10**6, "millones": 10**6,
    "mil millones": 10**9,
}  # fmt: skip
_NOT_FIGURES = re.compile(
    r"\b\d{1,2}(?=\s+de\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre"
    r"|setiembre|octubre|noviembre|diciembre)\b)"  # día del mes
    r"|\b\d{1,2}:\d{2}\b"  # hora
    r"|\b\d{1,2}\.?(?:o|a|os|as|er)\b"  # ordinal: 1.º, 3er (º → o al normalizar)
)
_NUMBER_WORDS = re.compile(
    r"\b(?:once|doce|trece|catorce|quince|dieci[a-z]+|veinte|veinti[a-z]+|treinta|cuarenta"
    r"|cincuenta|sesenta|setenta|ochenta|noventa|cien|ciento|(?:doscient|trescient|cuatrocient"
    r"|quinient|seiscient|setecient|ochocient|novecient)(?:os|as)|mil|millon(?:es)?"
    r"|millardos?|billon(?:es)?)\b"
)


@dataclass(frozen=True)
class Figure:
    start: int
    end: int
    value: Decimal
    unit: str
    step: Decimal  # medio paso del último dígito escrito, ya multiplicado


def mask(normalized: str, spans: Iterable[tuple[int, int]]) -> str:
    chars = list(normalized)
    for start, end in spans:
        chars[start:end] = " " * (end - start)
    return "".join(chars)


def _unit(match: re.Match[str]) -> str:
    token = match["unit"] or match["pre"] or ("e" if match["glued"] else None)
    if token is None:
        return "number"
    for unit, starts in (("EUR", "€e"), ("USD", "$du"), ("GBP", "£lg"), ("percent", "%")):
        if token[0] in starts:
            return unit
    if token.startswith("por"):
        return "percent"
    if token.startswith("pb") or (token.startswith("p.") and "b" in token) or "basico" in token:
        return "bp"
    return "pp"


def _parse(match: re.Match[str]) -> tuple[Decimal, Decimal]:
    """Valor y medio paso del último dígito, ya multiplicados."""
    num = match["num"]
    if _GROUPED.fullmatch(num):
        num = num.replace(".", "").replace(" ", "")
    num = num.replace(",", ".")
    decimals = len(num.split(".")[1]) if "." in num else 0
    sign = -1 if match["sign"] and match["sign"].strip() in "-−–" else 1
    word = match["k"] or (" ".join(match["mult"].split()) if match["mult"] else None)
    mult = Decimal(_MULTIPLIERS[word] if word else 1)
    return Decimal(num) * sign * mult, Decimal(5) * Decimal(10) ** -(decimals + 1) * mult


def extract_figures(normalized: str, exempt: Iterable[re.Pattern[str]]) -> list[Figure]:
    """Cifras del texto. No lo son los enteros sin unidad de 0 a 10, días, horas, ordinales y
    los nombres de `exempt` ("S&P 500", "G20")."""
    spans = [m.span() for m in _NOT_FIGURES.finditer(normalized)]
    for pattern in exempt:
        spans.extend(m.span() for m in pattern.finditer(normalized))
    figures: list[Figure] = []
    for match in _NUMBER.finditer(mask(normalized, spans)):
        value, step = _parse(match)
        unit = _unit(match)
        if unit == "number" and step == Decimal("0.5") and abs(value) <= 10:
            continue
        figures.append(Figure(*match.span(), value, unit, step))
    return figures


def number_words(normalized: str, figures: list[Figure]) -> list[tuple[int, int]]:
    """Números en palabras mayores que diez, fuera de las cifras ("42 mil" ya es una cifra)."""
    masked = mask(normalized, [(f.start, f.end) for f in figures])
    return [m.span() for m in _NUMBER_WORDS.finditer(masked)]


def is_currency(evidence: Evidence, currency: str = "EUR") -> bool:
    return evidence.unit.upper() in _CURRENCIES[currency]


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


def _distance(figure: Figure, evidence: Evidence) -> Decimal | None:
    """Distancia relativa a la tolerancia (≤ 1 casa) o `None` si no son comparables o no casan."""
    value, target, step = abs(figure.value), abs(evidence.value), figure.step
    candidates: list[tuple[Decimal, Decimal, Decimal]] = []  # (texto, evidencia, tolerancia)
    pp = _evidence_pp(evidence)
    if figure.unit in _CURRENCIES and (
        is_currency(evidence, figure.unit)
        or (figure.unit != "EUR" and evidence.unit.upper() in _UNITLESS)
    ):
        candidates.append((value, target, max(_EUR_TOL, target * _MONEY_REL_TOL, step)))
    if figure.unit in {"percent", "pp"} and pp is not None:
        candidates.append((value, pp, max(step, min(_PP_TOL, pp * _PCT_REL_TOL))))
    if figure.unit == "bp" and pp is not None:
        tol = max(step / _HUNDRED, min(_BP_TOL, pp * _PCT_REL_TOL))
        candidates.append((value / _HUNDRED, pp, tol))
    if figure.unit == "number":
        candidates.append((value, target, step))
        if pp is not None:
            candidates.append((value, pp, step))
    distances = [abs(text - goal) / tol for text, goal, tol in candidates if tol > 0]
    matching = [d for d in distances if d <= 1]
    return min(matching) if matching else None


def best_match(figure: Figure, evidence: list[Evidence]) -> Evidence | None:
    """La evidencia más cercana; a igualdad, la que tiene `calc_id`."""
    distances = [_distance(figure, item) for item in evidence]
    scored = [(d, evidence[i].calc_id is None, i) for i, d in enumerate(distances) if d is not None]
    return evidence[min(scored)[2]] if scored else None
