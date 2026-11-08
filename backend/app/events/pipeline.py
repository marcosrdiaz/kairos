"""Pipeline de un evento (diseño del MVP §2). Cada paso llama al `service.py` del módulo."""

import time
from datetime import UTC, datetime

from app.agents import service as agents_service
from app.agents.analyzer import AnalyzerError
from app.alerts import service as alerts_service
from app.core import clock
from app.events import repository
from app.impact import service as impact_service
from app.portfolio import service as portfolio_service
from app.schemas.agents import EventImpactStub
from app.schemas.common import SourceKind, SourceRef
from app.schemas.events import (
    Channel,
    CompanyRef,
    Direction,
    EventAnalysis,
    EventIn,
    EventObserved,
    EventType,
    Relevance,
    ReplayOut,
    SelectedBy,
    ShockSet,
)
from app.status import service as status_service

_MONTHS = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")
_FALLBACK_RATIONALE = "Movimiento observado en el mercado ese día"
_FALLBACK_MODEL = "fallback"


def _observed(event: EventIn) -> EventObserved:
    if event.observed is None:
        raise ValueError(f"El evento {event.id} no tiene `observed`")
    return event.observed


def _source(event: EventIn) -> SourceRef:
    day = event.occurred_at.astimezone(UTC)
    return SourceRef(
        kind=SourceKind.EVENT,
        label=f"Movimientos observados el {day.day} {_MONTHS[day.month - 1]} {day.year}",
        ref=event.id,
        as_of=datetime(day.year, day.month, day.day, tzinfo=UTC),
    )


def build_shockset(analysis: EventAnalysis, event: EventIn) -> ShockSet:
    """Magnitudes de `observed` para los canales elegidos. El analizador no aporta cifras."""
    observed = _observed(event)
    factors = {
        c.factor: observed.factors[c.factor]
        for c in analysis.channels
        if c.factor in observed.factors
    }
    moves = {
        c.key: observed.companies[c.key] for c in analysis.companies if c.key in observed.companies
    }
    if not moves and event.type is EventType.EARNINGS:
        moves = dict(observed.companies)
    if analysis.fallback or not (factors or moves):
        return ShockSet(
            event_id=event.id,
            factor_shocks=observed.factors,
            company_moves=observed.companies,
            selected_by=SelectedBy.ALL_OBSERVED,
            source=_source(event),
        )
    return ShockSet(
        event_id=event.id,
        factor_shocks=factors,
        company_moves=moves,
        selected_by=SelectedBy.ANALYZER,
        source=_source(event),
    )


def fallback_analysis(event: EventIn) -> EventAnalysis:
    """Respaldo sin LLM: todos los factores observados y la cadena que escribió un humano."""
    observed = _observed(event)
    labels = impact_service.default_channel_labels()
    return EventAnalysis(
        schema_version=1,
        event_id=event.id,
        event_type=event.type,
        entities=[],
        channels=[
            Channel(
                factor=factor,
                direction=Direction.UP if shock >= 0 else Direction.DOWN,
                label=labels[factor],
                rationale=_FALLBACK_RATIONALE,
            )
            for factor, shock in observed.factors.items()
        ],
        companies=[CompanyRef(key=key, name=key) for key in observed.companies],
        causal_chain=event.fallback_chain,
        relevance=Relevance.MEDIUM,
        analyzed_model=_FALLBACK_MODEL,
        fallback=True,
    )


def _analyze(event: EventIn) -> EventAnalysis:
    try:
        return agents_service.analyze_event(event)
    except AnalyzerError:
        return fallback_analysis(event)


def run(event: EventIn, occurred_at: datetime | None, silent: bool) -> ReplayOut:
    """`event` trae la fecha real del JSON; `occurred_at` es la que se muestra en la app."""
    started = time.perf_counter()
    analysis = _analyze(event)
    shocks = build_shockset(analysis, event)
    repository.save_event(event, occurred_at or clock.now(), analysis, clock.now())

    calc_ids: dict[str, str] = {}
    for portfolio_id in portfolio_service.list_portfolio_ids():
        impact = impact_service.compute_event_impact(portfolio_id, analysis, shocks)
        calc_ids[portfolio_id] = impact.calc_id
        stub = EventImpactStub.model_validate(
            impact.model_dump(mode="json", include=set(EventImpactStub.model_fields))
        )
        text, status = agents_service.write_event_explanation(stub)
        impact_service.attach_explanation(event.id, portfolio_id, text, status)
        status_service.recompute(portfolio_id)
        if not silent:
            alerts_service.evaluate(portfolio_id, event.id)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return ReplayOut(event_id=event.id, portfolios=calc_ids, elapsed_ms=elapsed_ms)
