"""Orquesta `explain_move`: junta el cambio real de valor, los ajustes de demo y los impactos de
los eventos del periodo, y deja la traza `move`. Los cálculos están en `move.py` (puro).

`by_asset` sale de `portfolio.get_value_change` (precios reales, sin flujos) más el ajuste de demo
de los eventos del periodo en los activos que siguen en cartera (D-031, D-075). `by_event` son los
`event_impact` calculados en la ventana; son estimaciones, no se suman a nada.
"""

from collections import defaultdict
from collections.abc import Callable, Iterable
from decimal import Decimal

from app.core import clock, trace
from app.impact import move
from app.portfolio import service as portfolio_service
from app.schemas.common import SourceRef, TraceKind
from app.schemas.impact import EventImpactOut, MoveAttributionOut, MoveEventImpact, MovePeriod
from app.schemas.portfolio import PortfolioOut

ImpactLister = Callable[[str, int], list[EventImpactOut]]


def _adjustments(valued: PortfolioOut, impacts: Iterable[EventImpactOut]) -> dict[str, Decimal]:
    """Ajuste de demo por activo, solo de los eventos del periodo y de los activos en cartera.

    Es el `breakdown` del impacto que generó cada ajuste (mismo `calc_id`), como en `get_valued`.
    """
    applied = {a.calc_id for a in valued.demo_adjustments}
    held = {p.asset_id for p in valued.positions}
    out: dict[str, Decimal] = defaultdict(Decimal)
    for impact in impacts:
        if impact.calc_id not in applied:
            continue
        for asset in impact.breakdown:
            if asset.asset_id in held:
                out[asset.asset_id] += asset.impact_eur
    return dict(out)


def _names(valued: PortfolioOut, impacts: Iterable[EventImpactOut]) -> dict[str, str]:
    names = {a.asset_id: a.name for i in impacts for a in i.breakdown}
    names.update({p.asset_id: p.name for p in valued.positions})
    return names


def _name(asset_id: str, known: dict[str, str]) -> str:
    """Nombre del activo; los vendidos en el periodo ya no están en la valoración."""
    if asset_id in known:
        return known[asset_id]
    found = next((a for a in portfolio_service.lookup_assets(asset_id) if a.id == asset_id), None)
    return found.name if found is not None else asset_id


def _sources(impacts: Iterable[EventImpactOut]) -> list[SourceRef]:
    unique: dict[tuple[str, str, str], SourceRef] = {}
    for impact in impacts:
        for ref in impact.sources:
            unique.setdefault((ref.kind, ref.ref, str(ref.as_of)), ref)
    return list(unique.values())


def explain_move(
    portfolio_id: str, period: MovePeriod, list_event_impacts: ImpactLister
) -> MoveAttributionOut:
    start, end = move.window(period, clock.now())
    change = portfolio_service.get_value_change(portfolio_id, start, end)  # 404 si no existe
    impacts = list_event_impacts(portfolio_id, move.PERIOD_DAYS[period])
    valued = portfolio_service.get_valued(portfolio_id)
    adjustments = _adjustments(valued, impacts)
    known = _names(valued, impacts)
    real = {a.asset_id: a for a in change.by_asset}
    assets = [
        move.AssetIn(
            asset_id=asset_id,
            name=_name(asset_id, known),
            start_value_eur=real[asset_id].start_value_eur if asset_id in real else Decimal(0),
            end_value_eur=real[asset_id].end_value_eur if asset_id in real else Decimal(0),
            flows_eur=real[asset_id].flows_eur if asset_id in real else Decimal(0),
            adjustment_eur=adjustments.get(asset_id, Decimal(0)),
        )
        for asset_id in sorted({*real, *adjustments})
    ]
    events = [
        MoveEventImpact(
            event_id=i.event_id,
            title=i.title,
            impact_eur=i.impact_eur,
            low_eur=i.low_eur,
            high_eur=i.high_eur,
        )
        for i in impacts
    ]
    result = move.attribute(assets, events)
    calc_id = trace.record(
        TraceKind.MOVE,
        move.FORMULA,
        inputs={
            "portfolio_id": portfolio_id,
            "period": period,
            "start": start,
            "end": end,
            "value_change": {a.asset_id: vars(a) for a in assets},
            "demo_adjustments": adjustments,
            "events": [e.model_dump() for e in events],
        },
        outputs={
            "change_eur": result.change_eur,
            "change_pct": result.change_pct,
            "by_asset": result.by_asset,
            "unexplained_eur": result.unexplained_eur,
        },
        sources=_sources(impacts),
        parent_calc_ids=[change.calc_id, *(i.calc_id for i in impacts)],
    )
    return MoveAttributionOut(
        period=period,
        start=start,
        end=end,
        change_eur=result.change_eur,
        change_pct=result.change_pct,
        by_asset=result.by_asset,
        by_event=events,
        unexplained_eur=result.unexplained_eur,
        calc_id=calc_id,
    )
