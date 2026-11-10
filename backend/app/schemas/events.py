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
    prompt_version: str | None = None
    """Versión del prompt del analizador con la que se hizo (T2-26, D-083): los primeros 12
    caracteres hexadecimales del SHA-256 del prompt. Si el prompt cambia, el análisis guardado deja
    de valer como caché y se vuelve a pedir. `null` en el respaldo y en los análisis anteriores."""

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


# --- Eventos pendientes de cierre (T4-04, D-089) ---


class EventStatus(StrEnum):
    PENDING_CLOSE = "pending_close"
    """La sesión que recoge el evento aún no ha cerrado: no hay shock medido ni cifras."""


class PendingEventOut(ContractModel):
    """Elemento de `GET /events/pending`: evento real cuyo impacto aún no se puede calcular.

    **No lleva ninguna cifra** (ni impacto, ni rango, ni `calc_id`): hasta el cierre solo se
    muestran la noticia y la cadena causal del analizador. Tras el cierre deja de salir aquí y
    aparece, con sus cifras, en `GET /portfolios/{id}/events`. Es igual para todas las carteras.
    `occurred_at` es cuándo ocurrió; `sources`, de dónde sale la noticia.
    """

    event_id: str
    title: str
    event_type: EventType
    occurred_at: UtcDatetime
    causal_chain: list[str]
    status: EventStatus
    sources: list[SourceRef]
