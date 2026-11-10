"""Regla del aviso por movimiento de mercado (`kind=market_move`, T2-21). Funciones puras.

Salta si la cartera varía en un día por encima del umbral de aviso **y** la parte de esa
variación que ningún evento explica (`unexplained_eur` de `explain_move`) también lo supera.
Usa la misma puntuación y el mismo umbral que `event_impact` (D-032).
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.alerts import engine


def score_if_alert(
    change_eur: Decimal, unexplained_eur: Decimal, total_eur: Decimal
) -> Decimal | None:
    """Puntuación del aviso, o `None` si no hay que avisar."""
    if not engine.is_significant(change_eur, total_eur):
        return None
    if not engine.is_significant(unexplained_eur, total_eur):
        return None
    return engine.score(unexplained_eur, total_eur)


def day_bounds(now: datetime) -> tuple[datetime, datetime]:
    """00:00 UTC del día de `now` (incluido) y del siguiente (excluido): un aviso por día."""
    start = now.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=1)
