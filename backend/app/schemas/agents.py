"""Contratos de agentes, guardián y /ask (diseño del MVP §4.4).

Este módulo también aloja tipos que otros contratos importan de aquí (ver *Peticiones de contrato*):
`ExplanationStatus`, `SentenceStatus` y `StatusState`.
"""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field

from app.schemas.common import (
    AssetClass,
    Confidence,
    ContractModel,
    Fraction,
    Money,
    Polarity,
    Profile,
    UtcDatetime,
)

# --- Estados compartidos ---


class ExplanationStatus(StrEnum):
    PENDING = "pending"
    OK = "ok"
    TEMPLATE = "template"


class SentenceStatus(StrEnum):
    OK = "ok"
    TEMPLATE = "template"


class StatusState(StrEnum):
    TRANQUILO = "tranquilo"
    ATENTO = "atento"
    REVISA_PLAN = "revisa_plan"


class StatusReasonKind(StrEnum):
    EVENT = "event"
    DRIFT = "drift"
    NONE = "none"


# --- /ask y SSE ---


class AskChannel(StrEnum):
    VOICE = "voice"
    TEXT = "text"


class AskRequest(ContractModel):
    question: str
    channel: AskChannel
    session_id: str


class AskMetaEvent(ContractModel):
    type: Literal["meta"]
    turn_id: str
    disclaimer: bool


class AskSentenceEvent(ContractModel):
    type: Literal["sentence"]
    turn_id: str
    index: int
    text: str
    calc_ids: list[str]
    portfolio_ids: list[str] = Field(default_factory=list)
    """Carteras a las que se refiere la frase (T4-09). Vacía si no habla de ninguna en concreto.
    Las cifras de carteras distintas nunca se suman."""


class AskDoneEvent(ContractModel):
    type: Literal["done"]
    turn_id: str
    fallback_used: bool
    blocked_count: int
    first_sentence_ms: int


class AskErrorEvent(ContractModel):
    type: Literal["error"]
    turn_id: str
    code: str
    message: str


AskEvent = Annotated[
    AskMetaEvent | AskSentenceEvent | AskDoneEvent | AskErrorEvent,
    Field(discriminator="type"),
]
"""Evento SSE del turno, discriminado por `type`. Orden: meta, sentence*, done (o error)."""


# --- Guardián ---


class GuardianChannel(StrEnum):
    VOICE = "voice"
    TEXT = "text"
    WIDGET = "widget"
    ALERT = "alert"
    EVENT_EXPLANATION = "event_explanation"


class QuestionKind(StrEnum):
    IMPACT = "impact"
    GENERAL = "general"


class GuardianReasonCode(StrEnum):
    FORBIDDEN_PATTERN = "FORBIDDEN_PATTERN"
    UNKNOWN_FIGURE = "UNKNOWN_FIGURE"
    TOO_LONG = "TOO_LONG"
    MISSING_EUR = "MISSING_EUR"


class Evidence(ContractModel):
    value: Fraction
    unit: str
    calc_id: str | None
    source: str | None


class GuardianRequest(ContractModel):
    text: str
    channel: GuardianChannel
    question_kind: QuestionKind | None
    sentence_index: int
    evidence: list[Evidence]


class GuardianReason(ContractModel):
    code: GuardianReasonCode
    detail: str


class GuardianFigure(ContractModel):
    text: str
    value: Fraction
    unit: str
    matched_calc_id: str | None


class GuardianVerdict(ContractModel):
    ok: bool
    reasons: list[GuardianReason]
    figures: list[GuardianFigure]


# --- Contexto precargado del explicador ---


class Fact(ContractModel):
    """Cifra ya calculada. `display` es el formato que el prompt pide copiar literalmente."""

    key: str
    label: str
    value: Fraction
    unit: str
    display: str
    calc_id: str


class ExplainerPlan(ContractModel):
    on_track: bool
    goal_year: int
    drift_exceeded: bool


class ExplainerEvent(ContractModel):
    event_id: str
    title: str
    causal_chain: list[str]
    polarity: Polarity
    confidence: Confidence
    top_assets: list[str]


class ExplainerStatus(ContractModel):
    state: StatusState


class ExplainerContext(ContractModel):
    portfolio_id: str
    as_of: UtcDatetime
    persona_hint: Profile
    facts: list[Fact]
    allocation: dict[str, Fraction]
    plan: ExplainerPlan
    events_7d: list[ExplainerEvent]
    status: ExplainerStatus


# --- Entradas de las funciones de redacción (`agents/service.py`) ---


class StatusFactsReason(ContractModel):
    kind: StatusReasonKind
    event_id: str | None


class StatusFacts(ContractModel):
    """Entrada de `write_status_sentence`. Todo son valores ya calculados: el LLM no opera.

    Los opcionales dependen del estado: `atento` usa `event_title`, `top_asset_class` o
    `main_channel` y `event_impact_eur`; `revisa_plan` usa `equity_current` y `equity_target`.
    """

    state: StatusState
    total_eur: Money
    change_week_pct: Fraction
    reason: StatusFactsReason
    event_title: str | None = None
    top_asset_class: AssetClass | None = None
    main_channel: str | None = None
    event_impact_eur: Money | None = None
    equity_current: Fraction | None = None
    equity_target: Fraction | None = None
    calc_id: str


class AssetImpactStub(ContractModel):
    asset_id: str
    name: str
    value_eur: Money
    impact_eur: Money
    market_eur: Money
    fx_eur: Money
    channel: str
    low_eur: Money | None = None
    """Rango por posición, como en `schemas.impact.AssetImpact` (T2-23)."""
    high_eur: Money | None = None


class EventImpactStub(ContractModel):
    """Entrada de `write_event_explanation` y `write_alert_message`.

    Sustituir por schemas.impact.EventImpactOut cuando T0-04 esté en main. Solo lleva los campos
    que necesita la redacción; sin ejemplo propio a propósito.
    """

    event_id: str
    portfolio_id: str
    title: str
    causal_chain: list[str]
    impact_eur: Money
    low_eur: Money
    high_eur: Money
    confidence: Confidence
    polarity: Polarity
    breakdown: list[AssetImpactStub]
    calc_id: str
