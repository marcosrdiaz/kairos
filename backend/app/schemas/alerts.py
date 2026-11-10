"""Avisos (diseño del MVP §4.4): `GET /portfolios/{id}/alerts`."""

from enum import StrEnum

from app.schemas.common import ContractModel, Fraction, UtcDatetime


class AlertKind(StrEnum):
    EVENT_IMPACT = "event_impact"
    DCA_PENDING = "dca_pending"
    DRIFT = "drift"
    MARKET_MOVE = "market_move"  # movimiento del día sin evento que lo explique (T2-21)


class AlertOut(ContractModel):
    id: str
    event_id: str | None
    kind: AlertKind
    score: Fraction
    message: str
    created_at: UtcDatetime
    delivered: bool
    calc_id: str | None
