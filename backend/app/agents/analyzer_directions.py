"""Dirección observada de cada factor para el analizador (T2-26, D-083). Funciones puras.

- `describe`: «OIL: sube, RATES_EUR: baja» para el prompt. Solo la dirección, nunca la magnitud
  (el modelo copiaría la cifra).
- `correct`: pone `channels[].direction` al signo observado. La dirección del modelo nunca gana al
  dato.
- `check_chain`: rechaza una cadena causal que dice lo contrario de lo observado («el petróleo
  baja» cuando subió). Es conservadora: solo mira frases que nombran un único factor y tienen un
  verbo de dirección claro; prefiere dejar pasar una frase dudosa a rechazar una buena. El rechazo
  vuelve al analizador como feedback para el reintento.

`RATES_EUR` es la rentabilidad del bono a diez años, no el tipo oficial del BCE: «el BCE baja los
tipos» puede ser cierto aunque la rentabilidad suba (ya estaba descontado), así que solo cuenta
«rentabilidad». `EURUSD` son dólares por euro: «el euro sube» es subir y «el dólar sube», bajar.
"""

import re
from collections.abc import Mapping
from decimal import Decimal

from app.schemas.common import Factor
from app.schemas.events import Channel, Direction

_UP = (
    "sube",
    "suben",
    "subió",
    "subieron",
    "subir",
    "al alza",
    "repunta",
    "repuntan",
    "se aprecia",
    "se encarece",
    "se encarecen",
    "más fuerte",
    "gana valor",
    "se fortalece",
)
_DOWN = (
    "baja",
    "bajan",
    "bajó",
    "bajaron",
    "cae",
    "caen",
    "cayó",
    "cayeron",
    "a la baja",
    "se deprecia",
    "se abarata",
    "se abaratan",
    "más débil",
    "pierde valor",
    "retrocede",
    "retroceden",
    "se debilita",
)

# Palabras de cada factor y si su verbo va al revés del factor (dólar frente a EURUSD).
_KEYWORDS: dict[Factor, tuple[tuple[str, bool], ...]] = {
    Factor.OIL: (("petróleo", False), ("crudo", False), ("brent", False)),
    Factor.EQ_US_TECH: (("tecnológicas", False),),
    Factor.EQ_GLOBAL: (
        ("bolsa mundial", False),
        ("bolsas mundiales", False),
        ("bolsa global", False),
        ("renta variable mundial", False),
    ),
    Factor.RATES_EUR: (("rentabilidad", False),),
    Factor.EURUSD: (
        ("el euro", False),
        ("del euro", False),
        ("el dólar", True),
        ("del dólar", True),
    ),
}

_WORDS = {
    Direction.UP: "sube",
    Direction.DOWN: "baja",
}


def _direction(value: Decimal) -> Direction | None:
    if value > 0:
        return Direction.UP
    if value < 0:
        return Direction.DOWN
    return None


def describe[K: str](moves: Mapping[K, Decimal]) -> str:
    """`clave: sube|baja|sin cambios`, por orden alfabético. Sin magnitudes."""
    parts = []
    for key in sorted(moves):
        direction = _direction(Decimal(moves[key]))
        parts.append(f"{key}: {_WORDS[direction] if direction else 'sin cambios'}")
    return ", ".join(parts)


def correct(channels: list[Channel], observed: Mapping[Factor, Decimal]) -> list[Channel]:
    """Cada canal con la dirección observada de su factor (si se movió)."""
    out: list[Channel] = []
    for channel in channels:
        direction = (
            _direction(Decimal(observed[channel.factor])) if channel.factor in observed else None
        )
        out.append(channel.model_copy(update={"direction": direction}) if direction else channel)
    return out


def _has(sentence: str, phrases: tuple[str, ...]) -> bool:
    return any(re.search(rf"(?<!\w){re.escape(p)}(?!\w)", sentence) for p in phrases)


def _claim(sentence: str) -> tuple[Factor, Direction] | None:
    """El factor y la dirección que afirma la frase, si nombra uno solo y la dirección es clara."""
    text = sentence.lower()
    found = [
        (factor, inverted)
        for factor, words in _KEYWORDS.items()
        for word, inverted in words
        if _has(text, (word,))
    ]
    factors = {factor for factor, _ in found}
    up, down = _has(text, _UP), _has(text, _DOWN)
    if len(factors) != 1 or up == down:
        return None
    factor = factors.pop()
    inverted = {inv for f, inv in found if f is factor}
    if len(inverted) != 1:
        return None
    said = Direction.UP if up else Direction.DOWN
    if inverted.pop():
        said = Direction.DOWN if said is Direction.UP else Direction.UP
    return factor, said


def check_chain(chain: list[str], observed: Mapping[Factor, Decimal]) -> None:
    """`ValueError` con el motivo si una frase contradice la dirección observada de un factor."""
    for sentence in chain:
        claim = _claim(sentence)
        if claim is None or claim[0] not in observed:
            continue
        factor, said = claim
        actual = _direction(Decimal(observed[factor]))
        if actual is not None and actual is not said:
            raise ValueError(
                f"la cadena dice que {factor.value} {_WORDS[said]}, pero ese día {_WORDS[actual]}"
                f" («{sentence}»)"
            )
