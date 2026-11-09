"""Radar de una cartera: reúne los datos de otros módulos (por su `service.py`), aplica las reglas
de `radar.py` y deja una traza por aviso. `get_exposure` llega por parámetro desde `service.py`
para no importarse en círculo (mismo patrón que `portfolio/plan_flow`).
"""

from collections.abc import Callable
from datetime import datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal

from app.core import trace
from app.core.errors import AppError
from app.exposure import radar, templates
from app.portfolio import service as portfolio_service
from app.prices import service as prices_service
from app.schemas.common import AssetClass, SourceRef, TraceKind
from app.schemas.exposure import ExposureOut
from app.schemas.portfolio import DcaPlanOut, DcaPlanStatus, PositionOut
from app.schemas.radar import RadarItem, RadarOut, RadarRule

_WEIGHT_STEP = Decimal("0.0001")
_PRICE_LOOKBACK = timedelta(days=7)

FORMULAS: dict[RadarRule, str] = {
    RadarRule.CONCENTRATION: "una empresa > 5 % o las 10 mayores > 25 % (look-through)",
    RadarRule.CURRENCY: "Σ exposición por divisa distinta de EUR y de la desconocida > 50 %",
    RadarRule.DRIFT: "|renta variable actual − objetivo del plan| > umbral del plan",
    RadarRule.REBALANCE_WITH_DCA: "n = (E − t·T) / (t·c − c_e), redondeado hacia arriba",
    RadarRule.CHEAPER_CONTRIBUTION: "precio actual / precio en la última aportación − 1 < −3 %",
    RadarRule.TAX_FREE_TRANSFER: "desviación del plan + fondo traspasable con plusvalía latente",
}


def _asset_info(asset_id: str, held: dict[str, PositionOut]) -> tuple[str, AssetClass]:
    if asset_id in held:
        return held[asset_id].name, held[asset_id].asset_class
    for asset in portfolio_service.lookup_assets(asset_id):
        if asset.id == asset_id:
            return asset.name, asset.asset_class
    return asset_id, AssetClass.MIXED


def _prices(
    asset_id: str, last_execution: datetime | None
) -> tuple[Decimal | None, Decimal | None, list[SourceRef]]:
    """Precio actual y el del día de la última aportación (último cierre hasta ese día)."""
    if last_execution is None:
        return None, None, []
    try:
        now = prices_service.latest(asset_id)
        day = last_execution.date()
        points = prices_service.history(asset_id, day - _PRICE_LOOKBACK, day)
    except AppError:
        return None, None, []
    if not points:
        return now.price, None, [now.source]
    return now.price, points[-1].price, [now.source, points[-1].source]


def _dca_input(
    plan: DcaPlanOut, held: dict[str, PositionOut]
) -> tuple[radar.DcaIn, list[SourceRef]]:
    sources: list[SourceRef] = []
    lines: list[radar.AllocationIn] = []
    for allocation in plan.allocations:
        name, asset_class = _asset_info(allocation.asset_id, held)
        now, then, used = _prices(allocation.asset_id, plan.last_execution_at)
        sources += used
        lines.append(
            radar.AllocationIn(allocation.asset_id, name, asset_class, allocation.weight, now, then)
        )
    return radar.DcaIn(plan.id, plan.amount_eur, tuple(lines)), sources


def get_radar(portfolio_id: str, get_exposure: Callable[[str], ExposureOut]) -> RadarOut:
    valued = portfolio_service.get_valued(portfolio_id)  # 404 si no existe
    exposure = get_exposure(portfolio_id)
    plan = portfolio_service.get_plan(portfolio_id)
    held = {p.asset_id: p for p in valued.positions}

    dca_plans: list[radar.DcaIn] = []
    price_sources: list[SourceRef] = []
    for dca in portfolio_service.list_dca_plans(portfolio_id):
        if dca.status is DcaPlanStatus.ACTIVE:
            built, used = _dca_input(dca, held)
            dca_plans.append(built)
            price_sources += used

    data = radar.RadarInput(
        portfolio_id=portfolio_id,
        total_eur=valued.total_eur,
        companies=tuple(
            radar.CompanyWeight(c.key, c.name, c.weight) for c in exposure.top_companies
        ),
        currencies={b.key: b.weight for b in exposure.by_currency},
        equity_weight=plan.current.equity,
        equity_target=plan.target.equity,
        drift_threshold=plan.drift_threshold,
        positions=tuple(
            radar.PositionIn(
                p.asset_id,
                p.name,
                p.asset_type,
                p.asset_class,
                p.transferable,
                p.unrealized_pnl_eur,
            )
            for p in valued.positions
        ),
        dca_plans=tuple(dca_plans),
    )
    parents = [exposure.calc_id, valued.calc_id, plan.calc_id]
    items: list[RadarItem] = []
    for finding in radar.evaluate(data):
        title, detail = templates.render(finding)
        weight = finding.weight
        calc_id = trace.record(
            TraceKind.RADAR,
            FORMULAS[finding.rule],
            inputs={"portfolio_id": portfolio_id, "rule": finding.rule, **finding.facts},
            outputs={
                "title": title,
                "detail": detail,
                "weight": weight,
                "value_eur": finding.value_eur,
            },
            sources=price_sources if finding.rule is RadarRule.CHEAPER_CONTRIBUTION else [],
            parent_calc_ids=parents,
        )
        suffix = f"_{finding.ref}" if finding.ref else ""
        items.append(
            RadarItem(
                id=f"rad_{finding.rule.value}{suffix}",
                kind=finding.kind,
                rule=finding.rule,
                title=title,
                detail=detail,
                value_eur=finding.value_eur,
                weight=None if weight is None else weight.quantize(_WEIGHT_STEP, ROUND_HALF_EVEN),
                user_rule=finding.user_rule,
                calc_id=calc_id,
            )
        )
    root = trace.record(
        TraceKind.RADAR,
        "radar = reglas de SPEC §8.5 sobre la exposición, el plan y el plan de aportaciones",
        inputs={"portfolio_id": portfolio_id},
        outputs={"items": [item.id for item in items]},
        sources=[],
        parent_calc_ids=[*(item.calc_id for item in items), exposure.calc_id],
    )
    return RadarOut(items=items, calc_id=root)
