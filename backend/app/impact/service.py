"""Interfaz pública del motor de impacto (diseño del MVP §4.2).

De momento todo delega en `mock.py`; T1-13 y T2-07 cambian cada función a la implementación real
sin cambiar su firma.
"""

from decimal import Decimal

from app.impact import mock
from app.schemas.common import Factor
from app.schemas.impact import (
    EventImpactOut,
    ExplanationStatus,
    MoveAttributionOut,
    MovePeriod,
    ScenarioOut,
)


def compute_event_impact(portfolio_id: str, analysis: object, shocks: object) -> EventImpactOut:
    """`analysis` es `EventAnalysis` y `shocks`, `ShockSet` (T0-05); T1-13 fija los tipos."""
    return mock.compute_event_impact(portfolio_id)


def attach_explanation(
    event_id: str, portfolio_id: str, text: str, status: ExplanationStatus
) -> None:
    """El mock no guarda nada."""


def estimate_scenario(portfolio_id: str, shocks: dict[Factor, Decimal]) -> ScenarioOut:
    return mock.estimate_scenario(portfolio_id)


def list_event_impacts(portfolio_id: str, days: int) -> list[EventImpactOut]:
    return mock.list_event_impacts(portfolio_id)


def explain_move(portfolio_id: str, period: MovePeriod) -> MoveAttributionOut:
    return mock.explain_move(portfolio_id, period)
