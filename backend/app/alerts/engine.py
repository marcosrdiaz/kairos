"""Reglas de los avisos (D-032). Funciones puras: entrada → salida, sin BD."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.alerts import config

FORMULA = (
    "score = |impacto| / max(150, 0,005 · patrimonio); aviso si score >= 1; "
    "máximo 2 avisos por semana ISO y cartera"
)


def threshold_eur(total_eur: Decimal) -> Decimal:
    return max(config.MIN_EUR, total_eur * config.MIN_SHARE)


def score(impact_eur: Decimal, total_eur: Decimal) -> Decimal:
    return abs(impact_eur) / threshold_eur(total_eur)


def is_significant(impact_eur: Decimal, total_eur: Decimal) -> bool:
    return score(impact_eur, total_eur) >= 1


def iso_week_bounds(now: datetime) -> tuple[datetime, datetime]:
    """Lunes 00:00 UTC (incluido) y lunes siguiente (excluido) de la semana ISO de `now`."""
    utc_now = now.astimezone(UTC)
    start = (utc_now - timedelta(days=utc_now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return start, start + timedelta(days=7)


def within_weekly_limit(sent_this_week: int) -> bool:
    return sent_this_week < config.WEEKLY_LIMIT
