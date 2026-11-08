"""Contratos del motor de impacto (diseño del MVP §4.3).

Ejemplos en `schemas/examples/<Modelo>.json` (y variantes `<Modelo>.<variante>.json`).
Convenciones de importes, fracciones y fechas: `schemas/common.py`.
"""

from enum import StrEnum
from typing import Literal

from app.schemas.common import (
    Confidence,
    ContractModel,
    Factor,
    Fraction,
    Money,
    Polarity,
    SourceRef,
    UtcDatetime,
)

EventType = Literal["central_bank", "commodity", "earnings", "fx", "macro"]
MovePeriod = Literal["day", "week", "month"]


class ExplanationStatus(StrEnum):
    PENDING = "pending"
    OK = "ok"
    TEMPLATE = "template"


class SurpriseLabel(StrEnum):
    MEJOR = "mejor"
    PEOR = "peor"
    EN_LINEA = "en_linea"


class AssetImpact(ContractModel):
    """`channel` es el `label` del canal con mayor contribución: "tipos", "resultados NVDA"..."""

    asset_id: str
    name: str
    value_eur: Money
    impact_eur: Money
    market_eur: Money
    fx_eur: Money
    channel: str


class Surprise(ContractModel):
    """Sin consenso, todos los campos son `null` (D-021)."""

    label: SurpriseLabel | None
    expected: str | None
    actual: str | None
    metric: str | None


class EventImpactOut(ContractModel):
    """`GET /portfolios/{id}/events`. `explanation` es `null` mientras está `pending`."""

    event_id: str
    portfolio_id: str
    title: str
    event_type: EventType
    occurred_at: UtcDatetime
    causal_chain: list[str]
    impact_eur: Money
    low_eur: Money
    high_eur: Money
    impact_pct: Fraction
    confidence: Confidence
    polarity: Polarity
    breakdown: list[AssetImpact]
    surprise: Surprise
    explanation: str | None
    explanation_status: ExplanationStatus
    sources: list[SourceRef]
    calc_id: str


class ScenarioRequest(ContractModel):
    """Cuerpo de `POST /portfolios/{id}/scenarios`."""

    factor_shocks: dict[Factor, Fraction]


class ScenarioOut(ContractModel):
    factor_shocks: dict[Factor, Fraction]
    impact_eur: Money
    low_eur: Money
    high_eur: Money
    confidence: Confidence
    breakdown: list[AssetImpact]
    calc_id: str


class MoveAssetChange(ContractModel):
    asset_id: str
    name: str
    change_eur: Money


class MoveEventImpact(ContractModel):
    """Estimación del impacto de un evento en el periodo."""

    event_id: str
    title: str
    impact_eur: Money
    low_eur: Money
    high_eur: Money


class MoveAttributionOut(ContractModel):
    """`GET /portfolios/{id}/move`. `unexplained_eur = change_eur − Σ by_event`."""

    period: MovePeriod
    start: UtcDatetime
    end: UtcDatetime
    change_eur: Money
    change_pct: Fraction
    by_asset: list[MoveAssetChange]
    by_event: list[MoveEventImpact]
    unexplained_eur: Money
    calc_id: str
