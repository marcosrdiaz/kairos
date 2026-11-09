"""Formato de cifras en español de España y evidencias del guardián (ver `facts.py`).

"42.380 euros", "61 %", "0,25 %": es el `display` que el prompt pide copiar literalmente. Sin
signo, porque el texto ya dice si sube o baja. Funciones puras.
"""

from collections.abc import Iterable
from decimal import ROUND_HALF_EVEN, Decimal

from app.agents import guardian
from app.schemas.agents import Evidence, Fact
from app.schemas.impact import Surprise

EUR = "EUR"
FRACTION = "fraction"
YEAR = "year"
NUMBER = "number"

_HUNDRED = Decimal(100)


# --- Formato ---


def _group(integer: int) -> str:
    return f"{integer:,}".replace(",", ".")


def _decimal_text(value: Decimal, places: int) -> str:
    """Valor positivo con `places` decimales como mucho, coma decimal y miles con punto."""
    rounded = value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN)
    integer, _, decimals = f"{rounded:f}".partition(".")
    decimals = decimals.rstrip("0")
    head = _group(int(integer))
    return f"{head},{decimals}" if decimals else head


def format_eur(value: Decimal) -> str:
    """Sin signo: el texto dice si sube o baja. Euros enteros salvo importes menores de 10."""
    amount = abs(value)
    return f"{_decimal_text(amount, 2 if amount < 10 else 0)} euros"


def format_fraction(value: Decimal) -> str:
    """Fracción como porcentaje sin signo: 0.76 → "76 %", 0.012 → "1,2 %", 0.0025 → "0,25 %"."""
    pct = abs(value) * _HUNDRED
    places = 2 if pct < 1 else 1 if pct < 10 else 0
    return f"{_decimal_text(pct, places)} %"


def format_number(value: Decimal) -> str:
    return _decimal_text(abs(value), 2)


def money(key: str, label: str, value: Decimal, calc_id: str) -> Fact:
    return Fact(
        key=key, label=label, value=value, unit=EUR, display=format_eur(value), calc_id=calc_id
    )


def fraction(key: str, label: str, value: Decimal, calc_id: str) -> Fact:
    return Fact(
        key=key,
        label=label,
        value=value,
        unit=FRACTION,
        display=format_fraction(value),
        calc_id=calc_id,
    )


def year(key: str, label: str, value: int, calc_id: str) -> Fact:
    return Fact(
        key=key, label=label, value=Decimal(value), unit=YEAR, display=str(value), calc_id=calc_id
    )


def number(key: str, label: str, value: Decimal, calc_id: str) -> Fact:
    return Fact(
        key=key,
        label=label,
        value=value,
        unit=NUMBER,
        display=format_number(value),
        calc_id=calc_id,
    )


# --- Evidencias del guardián ---


def as_evidence(facts: Iterable[Fact]) -> list[Evidence]:
    return [Evidence(value=f.value, unit=f.unit, calc_id=f.calc_id, source=None) for f in facts]


def text_evidence(texts: Iterable[str | None], source: str) -> list[Evidence]:
    """Números que ya trae un texto del evento (título, consenso) para que el explicador pueda
    citarlos: "0,25 puntos", "2025". Los extrae el propio guardián; no se calcula nada."""
    evidence: list[Evidence] = []
    for text in texts:
        if not text:
            continue
        for figure in guardian.extract_figures(guardian.normalize(text)):
            evidence.append(
                Evidence(value=figure.value, unit=figure.unit, calc_id=None, source=source)
            )
    return evidence


def surprise_evidence(surprise: Surprise, source: str) -> list[Evidence]:
    """Consenso del evento: esperado y real, en la unidad de su métrica (p. ej. pb)."""
    metric = (surprise.metric or "").lower()
    unit = "bp" if metric.endswith("_bp") else "percent" if metric.endswith("_pct") else NUMBER
    evidence: list[Evidence] = []
    for raw in (surprise.expected, surprise.actual):
        try:
            value = Decimal(raw) if raw is not None else None
        except ArithmeticError:
            value = None
        if value is not None:
            evidence.append(Evidence(value=value, unit=unit, calc_id=None, source=source))
    return evidence
