"""Avisos (diseño del MVP §4.4): `GET /portfolios/{id}/alerts`."""

from enum import StrEnum

from app.schemas.common import ContractModel, Fraction, UtcDatetime


class AlertKind(StrEnum):
    EVENT_IMPACT = "event_impact"
    DCA_PENDING = "dca_pending"
    DRIFT = "drift"
    MARKET_MOVE = "market_move"  # movimiento del día sin evento que lo explique (T2-21)
    NEWS_ESTIMATE = "news_estimate"  # impacto estimado de una noticia (T4-27, T4-31)


class AlertOut(ContractModel):
    """`news_id`: la noticia de un aviso `news_estimate` (T4-27); `null` en los demás."""

    id: str
    event_id: str | None
    kind: AlertKind
    score: Fraction
    message: str
    created_at: UtcDatetime
    delivered: bool
    calc_id: str | None
    news_id: str | None = None
