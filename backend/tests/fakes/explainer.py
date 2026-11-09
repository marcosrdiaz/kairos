"""Contexto precargado del explicador hecho con los ejemplos de `schemas/examples/`.

Sin BD: los tests del turno sustituyen `context.get` por esto para tener cifras fijas.
"""

from app.agents import context, facts
from app.core import clock
from app.schemas import examples
from app.schemas.agents import (
    ExplainerContext,
    ExplainerPlan,
    ExplainerStatus,
    Fact,
    StatusState,
)
from app.schemas.impact import EventImpactOut, MoveAttributionOut
from app.schemas.planning import ProjectionOut
from app.schemas.portfolio import PlanOut, PortfolioOut


def portfolio() -> PortfolioOut:
    return PortfolioOut.model_validate(examples.load("PortfolioOut"))


def plan() -> PlanOut:
    return PlanOut.model_validate(examples.load("PlanOut"))


def projection() -> ProjectionOut:
    return ProjectionOut.model_validate(examples.load("ProjectionOut"))


def events() -> list[EventImpactOut]:
    return [
        EventImpactOut.model_validate(examples.load(name))
        for name in ("EventImpactOut.nvda", "EventImpactOut")
    ]


def move() -> MoveAttributionOut:
    return MoveAttributionOut.model_validate(examples.load("MoveAttributionOut"))


def preloaded(*, with_events: bool = True, with_projection: bool = True) -> context.Preloaded:
    valued, the_plan = portfolio(), plan()
    the_projection = projection() if with_projection else None
    impacts = events() if with_events else []
    all_facts: list[Fact] = [*facts.portfolio_facts(valued), *facts.plan_facts(the_plan)]
    if the_projection is not None:
        all_facts += facts.projection_facts(the_projection)
    evidence = []
    for impact in impacts:
        all_facts += facts.event_impact_facts(impact)
        evidence += context.event_evidence(impact)
    ctx = ExplainerContext(
        portfolio_id="laura",
        as_of=clock.now(),
        persona_hint=valued.profile,
        facts=all_facts,
        allocation={"equity": valued.allocation.equity},
        plan=ExplainerPlan(on_track=True, goal_year=2040, drift_exceeded=False),
        events_7d=[context._event(impact) for impact in impacts],
        status=ExplainerStatus(state=StatusState.ATENTO),
    )
    return context.Preloaded(ctx, evidence, impacts, the_projection)


def fact(pre: context.Preloaded, key: str) -> Fact:
    found = pre.fact(key)
    assert found is not None, f"falta el fact {key}"
    return found
