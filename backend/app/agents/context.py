"""Contexto precargado del explicador (diseño del MVP §4.4, D-011).

Se construye por cartera llamando al `service.py` de cada módulo (nunca a sus tablas): patrimonio,
variación semanal, asignación, plan y proyección, eventos de los últimos 7 días con su impacto y
estado del widget. Va en el prompt con caché para que las 3 preguntas tipo se respondan sin
herramientas.

Caché en memoria por cartera. Se invalida cuando cambia el `calc_id` de `status` o, como red de
seguridad mientras `status` sea un mock, al cabo de `TTL_S` segundos. `invalidate` es pública
para que el pipeline de eventos (T2-09) la llame tras cada evento.
"""

import time
from dataclasses import dataclass, field
from threading import Lock

from app.agents import fact_format, facts
from app.core.errors import AppError
from app.impact import service as impact_service
from app.planning import service as planning_service
from app.portfolio import service as portfolio_service
from app.schemas.agents import (
    Evidence,
    ExplainerContext,
    ExplainerEvent,
    ExplainerPlan,
    ExplainerStatus,
    Fact,
    StatusState,
)
from app.schemas.impact import EventImpactOut
from app.schemas.planning import ProjectionOut
from app.schemas.portfolio import PlanOut
from app.status import service as status_service

EVENTS_DAYS = 7
TTL_S = 60.0
_TOP_ASSETS = 3


@dataclass(frozen=True)
class Preloaded:
    """El contrato `ExplainerContext` y las evidencias extra que no caben en él: los números
    que ya traen los textos de los eventos (título, consenso), que el texto puede citar."""

    context: ExplainerContext
    event_evidence: list[Evidence] = field(default_factory=list)
    events: list[EventImpactOut] = field(default_factory=list)
    projection: ProjectionOut | None = None

    def evidence(self) -> list[Evidence]:
        return [*fact_format.as_evidence(self.context.facts), *self.event_evidence]

    def fact(self, key: str) -> Fact | None:
        return next((f for f in self.context.facts if f.key == key), None)


@dataclass(frozen=True)
class _Entry:
    status_calc_id: str | None
    built_at: float
    preloaded: Preloaded


_cache: dict[str, _Entry] = {}
_lock = Lock()
_monotonic = time.monotonic  # reloj del TTL; los tests lo sustituyen


def _optional_plan(portfolio_id: str) -> PlanOut | None:
    try:
        return portfolio_service.get_plan(portfolio_id)
    except AppError:
        return None


def _optional_projection(portfolio_id: str) -> ProjectionOut | None:
    try:
        return planning_service.get_projection(portfolio_id)
    except AppError:
        return None


def _status(portfolio_id: str) -> tuple[StatusState | None, str | None]:
    try:
        status = status_service.get_status(portfolio_id)
    except AppError:
        return None, None
    return status.state, status.calc_id


def _event(impact: EventImpactOut) -> ExplainerEvent:
    top = sorted(impact.breakdown, key=lambda a: abs(a.impact_eur), reverse=True)[:_TOP_ASSETS]
    return ExplainerEvent(
        event_id=impact.event_id,
        title=impact.title,
        causal_chain=impact.causal_chain,
        polarity=impact.polarity,
        confidence=impact.confidence,
        top_assets=[asset.name for asset in top],
    )


def event_evidence(impact: EventImpactOut) -> list[Evidence]:
    source = f"event:{impact.event_id}"
    return [
        *fact_format.text_evidence([impact.title], source),
        *fact_format.surprise_evidence(impact.surprise, source),
    ]


def _plan(plan: PlanOut | None, projection: ProjectionOut | None) -> ExplainerPlan:
    drift = plan.drift_exceeded if plan else False
    goal_year = projection.goal_year if projection else (plan.goal_year if plan else None)
    on_track = projection.on_track if projection else not drift
    return ExplainerPlan(on_track=on_track, goal_year=goal_year or 0, drift_exceeded=drift)


def build(portfolio_id: str) -> Preloaded:
    """Construye el contexto sin caché. Lanza `AppError` si la cartera no se puede valorar."""
    portfolio = portfolio_service.get_valued(portfolio_id)
    plan = _optional_plan(portfolio_id)
    projection = _optional_projection(portfolio_id)
    impacts = impact_service.list_event_impacts(portfolio_id, EVENTS_DAYS)
    state, _ = _status(portfolio_id)

    all_facts = facts.portfolio_facts(portfolio)
    if plan is not None:
        all_facts += facts.plan_facts(plan)
    if projection is not None:
        all_facts += facts.projection_facts(projection)
    evidence: list[Evidence] = []
    for impact in impacts:
        all_facts += facts.event_impact_facts(impact)
        evidence += event_evidence(impact)

    allocation = portfolio.allocation
    context = ExplainerContext(
        portfolio_id=portfolio_id,
        as_of=portfolio.valued_at,  # no `clock.now()`: así el bloque no cambia y la caché del
        # prompt sigue valiendo mientras no cambien los datos
        persona_hint=portfolio.profile,
        facts=all_facts,
        allocation={
            "equity": allocation.equity,
            "fixed_income": allocation.fixed_income,
            "cash": allocation.cash,
            "mixed": allocation.mixed,
        },
        plan=_plan(plan, projection),
        events_7d=[_event(impact) for impact in impacts],
        status=ExplainerStatus(state=state or StatusState.TRANQUILO),
    )
    return Preloaded(context, evidence, impacts, projection)


def get(portfolio_id: str) -> Preloaded:
    """Contexto de la caché si sigue vigente; si no, lo reconstruye."""
    _, status_calc_id = _status(portfolio_id)
    now = _monotonic()
    with _lock:
        entry = _cache.get(portfolio_id)
    if entry and entry.status_calc_id == status_calc_id and now - entry.built_at < TTL_S:
        return entry.preloaded
    preloaded = build(portfolio_id)
    with _lock:
        _cache[portfolio_id] = _Entry(status_calc_id, now, preloaded)
    return preloaded


def invalidate(portfolio_id: str | None = None) -> None:
    """Olvida el contexto de una cartera (o de todas). La llama el pipeline tras un evento."""
    with _lock:
        if portfolio_id is None:
            _cache.clear()
        else:
            _cache.pop(portfolio_id, None)
