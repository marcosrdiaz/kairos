"""Contrato del estado de la cartera para el widget (diseño del MVP §4.3).

Ejemplos en `schemas/examples/StatusOut.json` y sus variantes, uno por estado.
"""

from app.schemas.agents import SentenceStatus, StatusReasonKind, StatusState
from app.schemas.common import ContractModel, Fraction, Money, UtcDatetime


class StatusReason(ContractModel):
    """`event_id` y `event_impact_eur` solo con `kind == "event"`."""

    kind: StatusReasonKind
    event_id: str | None
    event_impact_eur: Money | None


class StatusOut(ContractModel):
    """`GET /portfolios/{id}/status`. Se lee precalculado."""

    state: StatusState
    state_label: str
    total_eur: Money
    change_week_pct: Fraction
    sentence: str
    sentence_status: SentenceStatus
    reason: StatusReason
    price_as_of: UtcDatetime
    computed_at: UtcDatetime
    calc_id: str
