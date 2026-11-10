"""Interfaz pública de proyección y agenda (diseño del MVP §4.2, D-029).

`get_projection` es real (T1-14): lee el plan, la valoración y los DCA de `portfolio.service` y
los supuestos de `data/seed/assumptions.json`. `get_agenda` también (T2-06): lee
`data/events/agenda.json`, las betas de `impact.service`, el look-through de `exposure.service` y
los DCA de `portfolio.service`.
"""

import json
from datetime import datetime
from decimal import Decimal
from functools import cache
from pathlib import Path
from typing import Any

from app.core import clock, trace
from app.core.errors import AppError, ErrorCode
from app.exposure import service as exposure_service
from app.impact import service as impact_service
from app.planning import agenda, projection
from app.portfolio import service as portfolio_service
from app.schemas.common import Factor, SourceKind, SourceRef, TraceKind
from app.schemas.planning import AgendaItemOut, ProjectionOut, ProjectionScenario
from app.schemas.portfolio import DcaPlanOut, DcaPlanStatus

ASSUMPTIONS_FILE = Path(__file__).resolve().parents[3] / "data" / "seed" / "assumptions.json"
ASSUMPTIONS_REF = "data/seed/assumptions.json"
SCENARIOS = ("pesimista", "base", "optimista")
CLASSES = ("equity", "fixed_income", "cash")


@cache
def _assumptions() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(ASSUMPTIONS_FILE.read_text(encoding="utf-8"))
    return data


def _returns(scenario: str) -> dict[str, Decimal]:
    values = _assumptions()["scenarios"][scenario]
    return {cls: Decimal(values[cls]) for cls in CLASSES}


def _as_of() -> datetime:
    return datetime.fromisoformat(_assumptions()["as_of"])


def _goal_missing(portfolio_id: str) -> AppError:
    return AppError(
        ErrorCode.NOT_FOUND,
        "Esta cartera aún no tiene una meta (importe y año) para proyectar.",
        details={"portfolio_id": portfolio_id, "missing": "goal"},
    )


def get_projection(portfolio_id: str) -> ProjectionOut:
    """Proyección con DCA frente a la meta del plan (RF-22). Deja traza `projection`."""
    plan = portfolio_service.get_plan(portfolio_id)  # 404 si no hay cartera o plan
    if plan.goal_amount_eur is None or plan.goal_year is None:
        raise _goal_missing(portfolio_id)
    valued = portfolio_service.get_valued(portfolio_id)
    dca_plans = portfolio_service.list_dca_plans(portfolio_id)

    months = projection.months_until_goal(clock.now(), plan.goal_year)
    monthly = projection.monthly_contribution(
        (p.amount_eur, p.frequency, p.status == DcaPlanStatus.ACTIVE) for p in dca_plans
    )
    scenarios = []
    for name in SCENARIOS:
        rate = projection.blended_return(plan.target, _returns(name))
        value = projection.future_value(valued.total_eur, monthly, rate, months)
        scenarios.append(
            ProjectionScenario(
                name=name,
                annual_return=rate,
                value_at_goal_eur=value,
                reaches_goal=value >= plan.goal_amount_eur,
            )
        )
    base = scenarios[1]
    gap = projection.gap(plan.goal_amount_eur, base.value_at_goal_eur)

    assumptions_source = SourceRef(
        kind=SourceKind.ASSUMPTION,
        label="Supuestos de rentabilidad por clase de activo",
        ref=ASSUMPTIONS_REF,
        as_of=_as_of(),
    )
    plan_source = SourceRef(
        kind=SourceKind.USER_INPUT, label="Plan del usuario: meta y asignación objetivo", ref="plan"
    )
    calc_id = trace.record(
        TraceKind.PROJECTION,
        formula=(
            "r = Σ objetivo_clase × rentabilidad_clase; r_mes = (1 + r)^(1/12) − 1; "
            "V_{t+1} = V_t × (1 + r_mes) + aportación_mensual, durante los meses hasta "
            "diciembre del año de la meta; on_track = V_base ≥ meta"
        ),
        inputs={
            "current_value_eur": valued.total_eur,
            "monthly_contribution_eur": monthly,
            "months": months,
            "goal_amount_eur": plan.goal_amount_eur,
            "goal_year": plan.goal_year,
            "target": plan.target,
            "returns_by_class": {name: _returns(name) for name in SCENARIOS},
            "dca_plans": [
                {
                    "id": p.id,
                    "amount_eur": p.amount_eur,
                    "frequency": p.frequency,
                    "status": p.status,
                }
                for p in dca_plans
            ],
        },
        outputs={
            "scenarios": scenarios,
            "on_track": base.reaches_goal,
            "gap_eur": gap,
        },
        sources=[*_cited_sources(), plan_source],
        parent_calc_ids=[valued.calc_id, plan.calc_id],
    )
    return ProjectionOut(
        goal_amount_eur=plan.goal_amount_eur,
        goal_year=plan.goal_year,
        current_value_eur=valued.total_eur,
        monthly_contribution_eur=monthly,
        scenarios=scenarios,
        on_track=base.reaches_goal,
        gap_eur=gap,
        assumptions_source=assumptions_source,
        calc_id=calc_id,
    )


def _cited_sources() -> list[SourceRef]:
    """Las fuentes primarias de `assumptions.json` (Amundi CMA) para la traza."""
    return [SourceRef.model_validate(s) for s in _assumptions()["sources"]]


def get_agenda(portfolio_id: str) -> list[AgendaItemOut]:
    """Próximos eventos de `agenda.json` y aportaciones de los DCA activos, por fecha (T2-06).

    Cada cita deja una traza `agenda` que cuelga de la valoración de la cartera.
    """
    valued = portfolio_service.get_valued(portfolio_id)  # 404 si no existe
    values = {p.asset_id: p.value_eur for p in valued.positions}
    events = agenda.load_events()
    betas = impact_service.get_factor_betas(list(values))
    companies = {e.company for e in events if e.company is not None}
    weights = exposure_service.company_weights(list(values), companies)
    for p in valued.positions:  # la propia acción pesa 1 en sus resultados
        if p.ticker is not None and p.ticker in companies:
            weights.setdefault(p.asset_id, {})[p.ticker] = Decimal("1")

    now = clock.now()
    items = [
        _event_item(e, now, values, betas, weights, valued.total_eur, valued.calc_id)
        for e in events
    ]
    items += [
        _dca_item(p, valued.calc_id)
        for p in portfolio_service.list_dca_plans(portfolio_id)
        if p.status == DcaPlanStatus.ACTIVE
        and p.next_execution_at is not None
        and p.next_execution_at >= now
    ]
    return sorted(items, key=lambda item: item.date)


_AGENDA_SOURCE = SourceRef(
    kind=SourceKind.EVENT, label="Agenda de próximos eventos (ilustrativa)", ref=agenda.AGENDA_REF
)


def _event_item(
    event: agenda.AgendaEvent,
    now: datetime,
    values: dict[str, Decimal],
    betas: dict[str, dict[Factor, Decimal]],
    weights: dict[str, dict[str, Decimal]],
    total_eur: Decimal,
    valuation_calc_id: str,
) -> AgendaItemOut:
    date = agenda.event_date(now, event.offset_days, event.time_utc)
    if event.company is not None:
        exposed = agenda.company_exposure(values, weights, event.company)
        formula = f"exposed_eur = Σ V_i × peso de {event.company} en i (look-through)"
        inputs: dict[str, Any] = {
            "company": event.company,
            "positions": {
                a: {"value_eur": v, "weight": weights.get(a, {}).get(event.company)}
                for a, v in values.items()
            },
        }
        sources = [
            _AGENDA_SOURCE,
            SourceRef(
                kind=SourceKind.COMPOSITION, label="Composición de los fondos", ref="composition"
            ),
        ]
    else:
        exposed = agenda.factor_exposure(values, betas, event.factor)
        formula = f"exposed_eur = Σ V_i con |β_i,{event.factor}| ≥ {agenda.BETA_THRESHOLD}"
        inputs = {
            "factor": event.factor,
            "threshold": agenda.BETA_THRESHOLD,
            "positions": {
                a: {"value_eur": v, "beta": betas.get(a, {}).get(event.factor)}
                for a, v in values.items()
            },
        }
        sources = [
            _AGENDA_SOURCE,
            SourceRef(kind=SourceKind.BETA, label="Betas por factor", ref=event.factor.value),
        ]
    weight = agenda.exposed_weight(exposed, total_eur)
    calc_id = trace.record(
        TraceKind.AGENDA,
        formula=f"{formula}; exposed_weight = exposed_eur / valor total",
        inputs={
            **inputs,
            "event_id": event.id,
            "offset_days": event.offset_days,
            "now": now,
            "total_eur": total_eur,
        },
        outputs={"date": date, "exposed_eur": exposed, "exposed_weight": weight},
        sources=sources,
        parent_calc_ids=[valuation_calc_id],
    )
    return AgendaItemOut(
        date=date,
        kind=event.kind,
        title=event.title,
        factor=event.factor,
        exposed_weight=weight,
        exposed_eur=exposed,
        calc_id=calc_id,
    )


def _dca_item(plan: DcaPlanOut, valuation_calc_id: str) -> AgendaItemOut:
    assert plan.next_execution_at is not None
    calc_id = trace.record(
        TraceKind.AGENDA,
        formula="Próxima aportación del DCA activo: fecha e importe del plan",
        inputs={"dca_plan_id": plan.id, "frequency": plan.frequency, "day": plan.day},
        outputs={"date": plan.next_execution_at, "exposed_eur": plan.amount_eur},
        sources=[
            SourceRef(kind=SourceKind.USER_INPUT, label="Tu plan de aportaciones", ref=plan.id)
        ],
        parent_calc_ids=[valuation_calc_id],
    )
    return AgendaItemOut(
        date=plan.next_execution_at,
        kind="dca",
        title=agenda.dca_title(plan.frequency),
        factor=None,
        exposed_weight=None,
        exposed_eur=plan.amount_eur,
        calc_id=calc_id,
    )
