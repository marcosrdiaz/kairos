"""Interfaz pública de proyección y agenda (diseño del MVP §4.2, D-029).

`get_projection` es real (T1-14): lee el plan, la valoración y los DCA de `portfolio.service` y
los supuestos de `data/seed/assumptions.json`. `get_agenda` sigue en `mock.py` hasta T2-06.
"""

import json
from datetime import datetime
from decimal import Decimal
from functools import cache
from pathlib import Path
from typing import Any

from app.core import clock, trace
from app.core.errors import AppError, ErrorCode
from app.planning import mock, projection
from app.portfolio import service as portfolio_service
from app.schemas.common import SourceKind, SourceRef, TraceKind
from app.schemas.planning import AgendaItemOut, ProjectionOut, ProjectionScenario
from app.schemas.portfolio import DcaPlanStatus

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
    return mock.get_agenda(portfolio_id)
