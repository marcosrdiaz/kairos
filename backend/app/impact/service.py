"""Interfaz pública del motor de impacto (diseño del MVP §4.2)."""

from collections import defaultdict
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, cast

from app.core import clock, trace
from app.core.errors import AppError, ErrorCode
from app.events import service as events_service
from app.exposure import service as exposure_service
from app.impact import engine, move_flow, repository, scenario
from app.impact.betas import BetaEstimate
from app.portfolio import service as portfolio_service
from app.schemas.agents import ExplanationStatus
from app.schemas.common import AssetClass, AssetType, Factor, SourceKind, SourceRef, TraceKind
from app.schemas.events import Consensus, EventAnalysis, ShockSet
from app.schemas.impact import (
    AssetImpact,
    EventImpactOut,
    MoveAttributionOut,
    MovePeriod,
    ScenarioOut,
    Surprise,
)
from app.schemas.portfolio import AllocationOut, PortfolioOut, TargetAllocation

_PCT_STEP = Decimal("0.0001")


@dataclass(frozen=True)
class _Context:
    valued: PortfolioOut
    positions: list[engine.PositionIn]
    coverage: Decimal
    sources: list[SourceRef]
    parent_calc_ids: list[str]


def _midnight(day: date) -> datetime:
    return datetime(day.year, day.month, day.day, tzinfo=UTC)


def _load_context(portfolio_id: str, companies: Collection[str]) -> _Context:
    valued = portfolio_service.get_valued(portfolio_id)  # 404 si no existe
    exposure = exposure_service.get_exposure(portfolio_id)
    asset_ids = [p.asset_id for p in valued.positions]
    betas: dict[str, list[BetaEstimate]] = defaultdict(list)
    for estimate in repository.get_betas(asset_ids):
        betas[estimate.asset_id].append(estimate)
    weights = exposure_service.company_weights(asset_ids, companies)

    positions: list[engine.PositionIn] = []
    sources: list[SourceRef] = []
    for p in valued.positions:
        asset_weights = dict(weights.get(p.asset_id, {}))
        if p.asset_type is AssetType.STOCK and p.ticker in companies:
            asset_weights[cast(str, p.ticker)] = engine.ONE
        positions.append(
            engine.PositionIn(
                asset_id=p.asset_id,
                name=p.name,
                asset_class=p.asset_class,
                currency=p.price_currency,
                value_eur=p.value_eur,
                betas=betas[p.asset_id],
                company_weights=asset_weights,
            )
        )
        if betas[p.asset_id]:
            as_of = _midnight(betas[p.asset_id][0].window_end)
            label = f"Betas de {p.name}"
            sources.append(
                SourceRef(kind=SourceKind.BETA, label=label, ref=p.asset_id, as_of=as_of)
            )
        if p.asset_id in weights:
            label = f"Composición de {p.name}"
            sources.append(SourceRef(kind=SourceKind.COMPOSITION, label=label, ref=p.asset_id))
    parents = [valued.calc_id, exposure.calc_id]
    return _Context(valued, positions, exposure.coverage_pct, sources, parents)


def _trace_inputs(context: _Context) -> dict[str, Any]:
    return {
        "coverage_pct": context.coverage,
        "positions": [
            {
                "asset_id": p.asset_id,
                "currency": p.currency,
                "value_eur": p.value_eur,
                "company_weights": p.company_weights,
                "betas": {
                    b.factor: {"beta": b.beta, "std_err": b.std_err, "r2": b.r2} for b in p.betas
                },
            }
            for p in context.positions
        ],
    }


def _breakdown(result: engine.ImpactResult) -> list[AssetImpact]:
    return [
        AssetImpact(
            asset_id=a.asset_id,
            name=a.name,
            value_eur=a.value_eur,
            impact_eur=a.impact_eur,
            market_eur=a.market_eur,
            fx_eur=a.fx_eur,
            channel=a.channel,
            low_eur=a.low_eur,
            high_eur=a.high_eur,
        )
        for a in result.assets
    ]


def _under_target(current: AllocationOut, target: TargetAllocation) -> set[AssetClass]:
    pairs = {
        AssetClass.EQUITY: (current.equity, target.equity),
        AssetClass.FIXED_INCOME: (current.fixed_income, target.fixed_income),
        AssetClass.CASH: (current.cash, target.cash),
    }
    return {cls for cls, (now, goal) in pairs.items() if now < goal}


def _surprise(consensus: Consensus | None) -> Surprise:
    if consensus is None:
        return Surprise(label=None, expected=None, actual=None, metric=None)
    label = engine.surprise_label(consensus.metric, consensus.expected, consensus.actual)
    return Surprise(
        label=label,
        expected=consensus.expected,
        actual=consensus.actual,
        metric=consensus.metric,
    )


def _impact_pct(impact: Decimal, total: Decimal) -> Decimal:
    if total == engine.ZERO:
        return engine.ZERO
    return (impact / total).quantize(_PCT_STEP, rounding=ROUND_HALF_EVEN)


def compute_event_impact(
    portfolio_id: str, analysis: EventAnalysis, shocks: ShockSet
) -> EventImpactOut:
    """Calcula, deja traza y guarda el impacto. La fila `event` debe existir ya."""
    event = events_service.get_event(analysis.event_id)
    context = _load_context(portfolio_id, shocks.company_moves.keys())
    labels = {channel.factor: channel.label for channel in analysis.channels}
    result = engine.compute_impact(
        context.positions,
        engine.ShocksIn(shocks.factor_shocks, shocks.company_moves, labels),
        context.coverage,
    )
    under_target = _under_target(
        context.valued.allocation, portfolio_service.get_plan(portfolio_id).target
    )
    sources = [shocks.source, *context.sources]
    impact = EventImpactOut(
        event_id=analysis.event_id,
        portfolio_id=portfolio_id,
        title=event.title,
        event_type=analysis.event_type.value,
        occurred_at=event.occurred_at,
        causal_chain=[*analysis.causal_chain, engine.closing_link(result)],
        impact_eur=result.impact_eur,
        low_eur=result.low_eur,
        high_eur=result.high_eur,
        impact_pct=_impact_pct(result.impact_eur, context.valued.total_eur),
        confidence=result.confidence,
        polarity=engine.polarity(result, under_target),
        breakdown=_breakdown(result),
        surprise=_surprise(event.consensus),
        explanation=None,
        explanation_status=ExplanationStatus.PENDING,
        sources=sources,
        calc_id="",
        market_date=events_service.get_market_date(analysis.event_id),
        factor_moves=dict(shocks.factor_shocks),
    )
    calc_id = trace.record(
        TraceKind.EVENT_IMPACT,
        engine.FORMULA,
        inputs={
            **_trace_inputs(context),
            "factor_shocks": shocks.factor_shocks,
            "company_moves": shocks.company_moves,
            "selected_by": shocks.selected_by,
            "r2_weighted": result.r2,
        },
        outputs=impact.model_dump(mode="json", exclude={"calc_id"}),
        sources=sources,
        parent_calc_ids=context.parent_calc_ids,
    )
    stored = impact.model_copy(update={"calc_id": calc_id})
    repository.save_event_impact(stored)
    return stored


def attach_explanation(
    event_id: str, portfolio_id: str, text: str, status: ExplanationStatus
) -> None:
    if not repository.set_explanation(event_id, portfolio_id, text, status):
        raise AppError(
            ErrorCode.NOT_FOUND,
            "No hay impacto calculado para ese evento y esa cartera.",
            details={"event_id": event_id, "portfolio_id": portfolio_id},
        )


def estimate_scenario(portfolio_id: str, shocks: dict[Factor, Decimal]) -> ScenarioOut:
    context = _load_context(portfolio_id, ())
    result = scenario.estimate(context.positions, shocks, context.coverage)
    outcome: dict[str, Any] = {
        "factor_shocks": shocks,
        "impact_eur": result.impact_eur,
        "low_eur": result.low_eur,
        "high_eur": result.high_eur,
        "confidence": result.confidence,
        "breakdown": _breakdown(result),
    }
    calc_id = trace.record(
        TraceKind.SCENARIO,
        engine.FORMULA,
        inputs={**_trace_inputs(context), "factor_shocks": shocks, "r2_weighted": result.r2},
        outputs={k: v for k, v in outcome.items() if k != "factor_shocks"},
        sources=_scenario_sources(context.sources, shocks),
        parent_calc_ids=context.parent_calc_ids,
    )
    return ScenarioOut(**outcome, calc_id=calc_id)


def _scenario_sources(
    sources: Sequence[SourceRef], shocks: dict[Factor, Decimal]
) -> list[SourceRef]:
    ref = ",".join(sorted(shocks))
    return [SourceRef(kind=SourceKind.USER_INPUT, label="Escenario del usuario", ref=ref), *sources]


def list_event_impacts(portfolio_id: str, days: int) -> list[EventImpactOut]:
    """Impactos calculados en los últimos `days` días, del más reciente al más antiguo."""
    portfolio_service.ensure_exists(portfolio_id)  # 404 si no existe
    since = clock.now() - timedelta(days=days)
    impacts = []
    for row in repository.list_event_impacts(portfolio_id, since):
        record = trace.get(row.calc_id)
        if record is None:
            continue
        impacts.append(
            EventImpactOut.model_validate(
                {
                    **record.outputs,
                    "explanation": row.explanation,
                    "explanation_status": row.explanation_status,
                    "calc_id": row.calc_id,
                }
            )
        )
    return impacts


def default_channel_labels() -> Mapping[Factor, str]:
    """Etiqueta de cada factor cuando el analizador no da una (análisis de respaldo)."""
    return engine.DEFAULT_LABELS


def get_factor_betas(
    asset_ids: Collection[str],
) -> dict[str, dict[Factor, tuple[Decimal, Decimal]]]:
    """Betas guardadas por activo y factor (T1-12): `{asset_id: {factor: (β, error estándar)}}`.

    Sin fila, el activo no tiene beta en ese factor. La usa la agenda (T2-06).
    """
    betas: dict[str, dict[Factor, tuple[Decimal, Decimal]]] = defaultdict(dict)
    for estimate in repository.get_betas(asset_ids):
        betas[estimate.asset_id][estimate.factor] = (estimate.beta, estimate.std_err)
    return dict(betas)


def reset() -> None:
    """Borra los impactos guardados (`/demo/reset`)."""
    repository.delete_event_impacts()


def explain_move(portfolio_id: str, period: MovePeriod) -> MoveAttributionOut:
    """«¿Por qué ha bajado?»: cambio real del periodo por activo y eventos que lo explican.
    Deja traza `move`. Ver `move_flow.py` y `move.py`."""
    return move_flow.explain_move(portfolio_id, period, list_event_impacts)
