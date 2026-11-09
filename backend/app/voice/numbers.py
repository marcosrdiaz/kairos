"""Cifras a palabras para el TTS (D-043): Flash v2.5 no normaliza el texto y lee mal las cifras.

Se aplica **después** del guardián (que valida las cifras en dígitos contra `calc_trace`) y
**solo al audio**: el texto en pantalla conserva los dígitos. Función pura y determinista.

Cubre importes (€ y $, con miles, decimales y multiplicadores «k», «M», «millones», «mil»),
porcentajes, puntos («pp», «pb», «puntos»), signos, rangos («300–640»), fechas
(«5 de junio de 2025», «26/02/2025», «2025-06-13») y horas («18:00»). Lo que va pegado a
letras (ISIN, «T1-21») se deja como está.
"""

import re
from decimal import Decimal

_UNITS = (
    "cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince "
    "dieciséis diecisiete dieciocho diecinueve veinte veintiuno veintidós veintitrés "
    "veinticuatro veinticinco veintiséis veintisiete veintiocho veintinueve"
).split()
_TENS = {3: "treinta", 4: "cuarenta", 5: "cincuenta", 6: "sesenta", 7: "setenta",
         8: "ochenta", 9: "noventa"}  # fmt: skip
_HUNDREDS = {1: "ciento", 2: "doscientos", 3: "trescientos", 4: "cuatrocientos",
             5: "quinientos", 6: "seiscientos", 7: "setecientos", 8: "ochocientos",
             9: "novecientos"}  # fmt: skip
_MONTHS = ("enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre "
           "diciembre").split()  # fmt: skip
_MILLION = 10**6

# Sustantivos que cambian «uno» por «un» (masculino) o por «una» y «-ientas» (femenino).
_MASC_NOUNS = re.compile(
    r"(?:euros?|d[oó]lar(?:es)?|puntos?|c[eé]ntimos?|años?|d[ií]as?|mes(?:es)?|fondos?|"
    r"activos?|valores?|millones|mill[oó]n)$"
)
_FEM_NOUNS = re.compile(
    r"(?:acci[oó]n(?:es)?|participaci[oó]n(?:es)?|semanas?|empresas?|posici[oó]n(?:es)?|"
    r"compañ[ií]as?|horas?|libras?)$"
)

_DATE_DMY = re.compile(r"(?<![\w/])(\d{1,2})/(\d{1,2})/(\d{4})(?![\w/])")
_DATE_ISO = re.compile(r"(?<![\w-])(\d{4})-(\d{2})-(\d{2})(?![\w-])")
_TIME = re.compile(r"(?<![\w:.,])(\d{1,2}):(\d{2})(?![\w:])")
_RANGE = re.compile(r"(?<![\w.,])(\d[\d.,]*)\s?[-–]\s?(?=\d)")
_NUMBER = re.compile(
    r"(?<![\w.,/:])(?<!\w[-–−])(?P<sign>[-+−–]\s?)?"
    r"(?P<num>\d{1,3}(?:\.\d{3})+(?:,\d+)?(?!\d)|\d{1,3}(?: \d{3})+(?:,\d+)?(?!\d)|\d+(?:,\d+)?)"
    r"(?:\s?(?P<k>k|M|mm)(?!\w)|\s+(?P<mult>mil\s+millones|millones|mill[oó]n|mil)\b)?"
    r"(?P<unit>\s?(?:€|\$|%)|\s+(?:de\s+)?(?:euros?|eur|d[oó]lar(?:es)?|usd|por\s+ciento"
    r"|puntos?\s+b[aá]sicos|pb|puntos?\s+porcentuales|pp)(?!\w))?"
    r"(?!\w)"
)
_NEXT_WORD = re.compile(r"\s+([^\W\d_]+)")
_MULTIPLIERS = {"k": 10**3, "mil": 10**3, "m": _MILLION, "mm": _MILLION, "millon": _MILLION,
                "millón": _MILLION, "millones": _MILLION, "mil millones": 10**9}  # fmt: skip


def _below_thousand(n: int) -> str:
    if n == 100:
        return "cien"
    if n < 30:
        return _UNITS[n]
    if n < 100:
        tens, unit = divmod(n, 10)
        return _TENS[tens] + (f" y {_UNITS[unit]}" if unit else "")
    hundreds, rest = divmod(n, 100)
    return _HUNDREDS[hundreds] + (f" {_below_thousand(rest)}" if rest else "")


def _apocope(words: str) -> str:
    """«uno» → «un» al final (veintiuno → veintiún), delante de un sustantivo masculino."""
    if words.endswith("veintiuno"):
        return words[: -len("veintiuno")] + "veintiún"
    if words == "uno" or words.endswith(" uno"):
        return words[:-1]
    return words


def _feminine(words: str) -> str:
    words = words.replace("ientos", "ientas")
    if words == "uno" or words.endswith(("veintiuno", " uno")):
        return words[:-1] + "a"
    return words


def integer_to_words(n: int, form: str = "plain") -> str:
    """Entero ≥ 0 en palabras. `form`: `plain` («veintiuno»), `masc` («veintiún»), `fem`."""
    if n == 0:
        return "cero"
    millions, rest = divmod(n, _MILLION)
    thousands, units = divmod(rest, 1000)
    parts: list[str] = []
    if millions:
        parts.append(
            "un millón" if millions == 1 else f"{_apocope(integer_to_words(millions))} millones"
        )
    low: list[str] = []
    if thousands:
        low.append("mil" if thousands == 1 else f"{_apocope(_below_thousand(thousands))} mil")
    if units:
        low.append(_below_thousand(units))
    low_words = " ".join(low)
    if low_words and form == "fem":
        low_words = _feminine(low_words)
    elif low_words and form == "masc":
        low_words = _apocope(low_words)
    elif not low_words and form == "masc":
        parts = [_apocope(p) for p in parts]
    return " ".join([*parts, low_words] if low_words else parts)


def _fraction_to_words(digits: str) -> str:
    """Parte decimal tras «coma»: «05» → «cero cinco», «25» → «veinticinco»."""
    zeros = len(digits) - len(digits.lstrip("0"))
    rest = digits.lstrip("0")
    words = ["cero"] * zeros + ([integer_to_words(int(rest))] if rest else [])
    return " ".join(words)


def _unit_kind(unit: str | None) -> str | None:
    if not unit:
        return None
    u = unit.strip().lower()
    if u in ("€", "eur") or u.endswith(("euro", "euros")):
        return "EUR"
    if u in ("$", "usd") or "lar" in u:
        return "USD"
    if u == "%" or u.startswith("por"):
        return "percent"
    if u == "pb" or "sicos" in u:
        return "bp"
    return "pp"


def _form_from_next_word(text: str, end: int) -> str:
    match = _NEXT_WORD.match(text, end)
    if match is None:
        return "plain"
    word = match.group(1).lower()
    if _FEM_NOUNS.fullmatch(word):
        return "fem"
    if _MASC_NOUNS.fullmatch(word):
        return "masc"
    return "plain"


def _currency(value: Decimal, decimals: str, names: tuple[str, str, str]) -> str:
    singular, plural, cents = names
    integer = int(value)
    if decimals and len(decimals) == 2 and int(decimals):
        n_cents = int(decimals)
        name = singular if integer == 1 else plural
        cent_name = cents[:-1] if n_cents == 1 else cents
        return (f"{integer_to_words(integer, 'masc')} {name} con "
                f"{integer_to_words(n_cents, 'masc')} {cent_name}")  # fmt: skip
    if decimals and int(decimals):
        return f"{_decimal_words(value)} {plural}"
    name = singular if integer == 1 else plural
    exact_millions = integer >= _MILLION and integer % _MILLION == 0
    return f"{integer_to_words(integer, 'masc')} {'de ' if exact_millions else ''}{name}"


def _decimal_words(value: Decimal, form: str = "plain") -> str:
    integer_part, _, frac = f"{value:f}".partition(".")
    frac = frac.rstrip("0")
    if not frac:
        return integer_to_words(int(integer_part), form)
    return f"{integer_to_words(int(integer_part))} coma {_fraction_to_words(frac)}"


def _replace_number(match: re.Match[str]) -> str:
    raw = match["num"].replace(".", "").replace(" ", "")
    integer_part, _, decimals = raw.partition(",")
    value = Decimal(f"{integer_part}.{decimals}" if decimals else integer_part)
    mult_word = match["k"] or (" ".join(match["mult"].split()) if match["mult"] else None)
    if mult_word:
        value *= _MULTIPLIERS[mult_word if mult_word in _MULTIPLIERS else mult_word.lower()]
        decimals = "" if value == value.to_integral_value() else decimals
        value = value.normalize() if decimals else Decimal(int(value))
    sign = ""
    if match["sign"]:
        sign = "más " if match["sign"].strip() == "+" else "menos "
    kind = _unit_kind(match["unit"])
    if kind == "EUR":
        return sign + _currency(value, decimals, ("euro", "euros", "céntimos"))
    if kind == "USD":
        return sign + _currency(value, decimals, ("dólar", "dólares", "centavos"))
    if kind == "percent":
        return f"{sign}{_decimal_words(value)} por ciento"
    if kind in ("pp", "bp"):
        suffix = "puntos porcentuales" if kind == "pp" else "puntos básicos"
        return f"{sign}{_decimal_words(value, 'masc')} {suffix}"
    form = _form_from_next_word(match.string, match.end())
    words = _decimal_words(value, form)
    if mult_word and not decimals and value % 1000 == 0:
        words = integer_to_words(int(value), form)
    return sign + words


def _replace_dmy(match: re.Match[str]) -> str:
    day, month, year = (int(g) for g in match.groups())
    if not (1 <= day <= 31 and 1 <= month <= 12):
        return match.group(0)
    return f"{integer_to_words(day)} de {_MONTHS[month - 1]} de {integer_to_words(year)}"


def _replace_iso(match: re.Match[str]) -> str:
    year, month, day = (int(g) for g in match.groups())
    if not (1 <= day <= 31 and 1 <= month <= 12):
        return match.group(0)
    return f"{integer_to_words(day)} de {_MONTHS[month - 1]} de {integer_to_words(year)}"


def _replace_time(match: re.Match[str]) -> str:
    hour, minute = int(match.group(1)), int(match.group(2))
    if hour > 23 or minute > 59:
        return match.group(0)
    if minute == 0:
        return f"{integer_to_words(hour)} horas"
    return f"{integer_to_words(hour)} y {integer_to_words(minute)}"


def spell_out(text: str) -> str:
    """Texto con las cifras escritas en palabras, listo para el TTS."""
    text = _DATE_DMY.sub(_replace_dmy, text)
    text = _DATE_ISO.sub(_replace_iso, text)
    text = _TIME.sub(_replace_time, text)
    text = _RANGE.sub(r"\1 a ", text)
    return _NUMBER.sub(_replace_number, text)
