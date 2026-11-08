"""Contratos de proyección y agenda (diseño del MVP §4.3, D-029).

Ejemplos en `schemas/examples/ProjectionOut.json` y `AgendaItemOut.json` (y su variante `dca`).
"""

from typing import Literal

from app.schemas.common import ContractModel, Factor, Fraction, Money, SourceRef, UtcDatetime
from app.schemas.impact import EventType


class ProjectionScenario(ContractModel):
    name: Literal["pesimista", "base", "optimista"]
    annual_return: Fraction
    value_at_goal_eur: Money
    reaches_goal: bool


class ProjectionOut(ContractModel):
    """`GET /portfolios/{id}/projection`. `on_track` equivale a que `base` alcanza la meta."""

    goal_amount_eur: Money
    goal_year: int
    current_value_eur: Money
    monthly_contribution_eur: Money
    scenarios: list[ProjectionScenario]
    on_track: bool
    gap_eur: Money
    assumptions_source: SourceRef
    calc_id: str


class AgendaItemOut(ContractModel):
    """`GET /portfolios/{id}/agenda` devuelve una lista. Un DCA no tiene `factor` ni peso."""

    date: UtcDatetime
    kind: EventType | Literal["dca"]
    title: str
    factor: Factor | None
    exposed_weight: Fraction | None
    exposed_eur: Money | None
    calc_id: str
