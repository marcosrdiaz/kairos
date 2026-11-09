"""Reglas del estado del widget (`SPEC.md` §8.6). Funciones puras: entrada → salida, sin BD."""

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from app.schemas.agents import StatusState
from app.schemas.impact import EventImpactOut
from app.status import config

FORMULA = (
    "atento si hay un evento en las últimas 72 h con |impacto| >= max(150, 0,5 % del patrimonio); "
    "si no, revisa_plan si |equity - target_equity| > drift_threshold; si no, tranquilo"
)


def is_significant(impact_eur: Decimal, total_eur: Decimal) -> bool:
    return abs(impact_eur) >= max(config.ATENTO_MIN_EUR, total_eur * config.ATENTO_MIN_SHARE)


def evaluate(
    total_eur: Decimal,
    impacts: Sequence[EventImpactOut],
    *,
    drift_exceeded: bool,
    now: datetime,
) -> tuple[StatusState, EventImpactOut | None]:
    """Estado y, si es `atento`, el evento significativo más reciente. Cuenta la fecha del evento
    (`occurred_at`), no la del cálculo: la precarga del guion se calcula hoy con fecha de hace 96 h.
    """
    since = now - config.ATENTO_WINDOW
    significant = [
        impact
        for impact in impacts
        if impact.occurred_at >= since and is_significant(impact.impact_eur, total_eur)
    ]
    if significant:
        return StatusState.ATENTO, max(significant, key=lambda impact: impact.occurred_at)
    return (StatusState.REVISA_PLAN if drift_exceeded else StatusState.TRANQUILO), None
