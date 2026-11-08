"""Contratos de eventos y analizador (diseño del MVP §4.2).

- `EventIn`: formato de `data/events/replay/<id>.json` (lo escribe un humano; `observed` lo calcula
  T1-09, así que puede faltar al principio).
- `EventAnalysis`: salida del analizador. **No contiene ningún número**: un validador rechaza
  dígitos en los textos, salvo `title`, que viene del JSON del evento.
- `ShockSet`: lo construye `events` de forma determinista y entra en el motor de impacto.
"""

import re
from enum import StrEnum
from typing import Literal

from pydantic import field_validator

from app.schemas.common import ContractModel, Factor, Fraction, SourceRef, UtcDatetime

_DIGIT = re.compile(r"\d")


class EventType(StrEnum):
    CENTRAL_BANK = "central_bank"
    COMMODITY = "commodity"
    EARNINGS = "earnings"
    FX = "fx"
    MACRO = "macro"


class EntityKind(StrEnum):
    CENTRAL_BANK = "central_bank"
    COMPANY = "company"
    COMMODITY = "commodity"
    CURRENCY = "currency"
    COUNTRY = "country"


class Direction(StrEnum):
    UP = "up"
    DOWN = "down"


class Relevance(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SelectedBy(StrEnum):
    ANALYZER = "analyzer"
    ALL_OBSERVED = "all_observed"


# --- Evento de replay ---


class EventObserved(ContractModel):
    """Movimientos observados ese día. `companies` usa la misma clave que `constituent_key`."""

    factors: dict[Factor, Fraction]
    companies: dict[str, Fraction]


class Consensus(ContractModel):
    """Consenso del mercado para medir la sorpresa. Solo el BCE lo lleva (D-021)."""

    metric: str
    expected: str
    actual: str
    source: str


class EventIn(ContractModel):
    id: str
    type: EventType
    title: str
    occurred_at: UtcDatetime
    text: str
    source_urls: list[str]
    observed: EventObserved | None = None
    observed_source: str | None = None
    consensus: Consensus | None = None
    fallback_chain: list[str]
    illustrative: bool


# --- Analizador ---


def _no_digits(value: str) -> str:
    if _DIGIT.search(value):
        raise ValueError("El análisis no puede contener cifras")
    return value


class Entity(ContractModel):
    kind: EntityKind
    key: str
    name: str

    _name_has_no_digits = field_validator("name")(_no_digits)


class Channel(ContractModel):
    factor: Factor
    direction: Direction
    label: str
    rationale: str

    _text_has_no_digits = field_validator("label", "rationale")(_no_digits)


class CompanyRef(ContractModel):
    key: str
    name: str

    _name_has_no_digits = field_validator("name")(_no_digits)


class EventAnalysis(ContractModel):
    schema_version: Literal[1]
    event_id: str
    event_type: EventType
    entities: list[Entity]
    channels: list[Channel]
    companies: list[CompanyRef]
    causal_chain: list[str]
    relevance: Relevance
    analyzed_model: str
    fallback: bool

    @field_validator("causal_chain")
    @classmethod
    def _chain_has_no_digits(cls, value: list[str]) -> list[str]:
        for step in value:
            _no_digits(step)
        return value


class ShockSet(ContractModel):
    event_id: str
    factor_shocks: dict[Factor, Fraction]
    company_moves: dict[str, Fraction]
    selected_by: SelectedBy
    source: SourceRef


# --- Control de replay (POST /demo/replay/{event_id}) ---


class ReplayRequest(ContractModel):
    """Cuerpo opcional. `occurred_at` fecha el evento en ese instante en vez de `now()`; con
    `silent` no se generan avisos."""

    occurred_at: UtcDatetime | None = None
    silent: bool = False


class ReplayOut(ContractModel):
    """Resultado de inyectar un evento: la traza del impacto por cartera y lo que tardó."""

    event_id: str
    portfolios: dict[str, str]
    elapsed_ms: int
