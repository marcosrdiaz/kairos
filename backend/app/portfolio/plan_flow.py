"""Orquesta el plan de inversión (RF-22): lee o guarda el plan, valora y deja la traza `plan`.

Los cálculos están en `plan.py` (puro) y la tabla en `plan_store.py`. `service.py` solo delega.
"""

from collections.abc import Callable
from decimal import Decimal

from app.core import trace
from app.core.db import session_scope
from app.portfolio import errors, plan, plan_store, repository
from app.portfolio.plan_store import StoredPlan
from app.schemas.common import AssetClass, SourceKind, SourceRef, TraceKind
from app.schemas.portfolio import PlanOut, PlanUpdateRequest, PortfolioOut

Valuer = Callable[[str], PortfolioOut]


def _load(portfolio_id: str) -> StoredPlan | None:
    with session_scope() as session:
        if repository.get_portfolio(session, portfolio_id) is None:
            raise errors.portfolio_not_found(portfolio_id)
        return plan_store.get(session, portfolio_id)


def get(portfolio_id: str, get_valued: Valuer) -> PlanOut:
    stored = _load(portfolio_id)
    if stored is None:
        raise errors.plan_not_found(portfolio_id)
    return _assess(portfolio_id, stored, get_valued)


def update(portfolio_id: str, request: PlanUpdateRequest, get_valued: Valuer) -> PlanOut:
    """Guarda el objetivo enviado. Los campos que no vienen en la petición conservan su valor
    (o el valor por defecto, si la cartera aún no tenía plan)."""
    previous = _load(portfolio_id)
    sent = request.model_fields_set
    stored = StoredPlan(
        target=request.target,
        drift_threshold=request.drift_threshold,
        goal_amount_eur=request.goal_amount_eur,
        goal_year=request.goal_year,
    )
    if previous is not None:
        stored = StoredPlan(
            target=request.target,
            drift_threshold=(
                stored.drift_threshold if "drift_threshold" in sent else previous.drift_threshold
            ),
            goal_amount_eur=(
                stored.goal_amount_eur if "goal_amount_eur" in sent else previous.goal_amount_eur
            ),
            goal_year=stored.goal_year if "goal_year" in sent else previous.goal_year,
        )
    reason = plan.target_error(stored.target, stored.drift_threshold)
    if reason is not None:
        raise errors.plan_invalid(reason)
    with session_scope() as session:
        plan_store.save(session, portfolio_id, stored)
    return _assess(portfolio_id, stored, get_valued)


def _assess(portfolio_id: str, stored: StoredPlan, get_valued: Valuer) -> PlanOut:
    valued = get_valued(portfolio_id)
    by_class: dict[AssetClass, Decimal] = {}
    for position in valued.positions:
        by_class[position.asset_class] = (
            by_class.get(position.asset_class, Decimal(0)) + position.value_eur
        )
    current = plan.current_allocation(by_class)
    check = plan.assess(stored.target, stored.drift_threshold, current)
    calc_id = trace.record(
        TraceKind.PLAN,
        plan.FORMULA,
        inputs={
            "portfolio_id": portfolio_id,
            "target": stored.target,
            "drift_threshold": stored.drift_threshold,
            "value_eur_by_class": by_class,
            "total_eur": valued.total_eur,
        },
        outputs={
            "current": current,
            "drift_equity": check.drift_equity,
            "drift_exceeded": check.drift_exceeded,
        },
        sources=[
            SourceRef(
                kind=SourceKind.USER_INPUT,
                label="Plan de inversión de la cartera",
                ref=portfolio_id,
                as_of=None,
            )
        ],
        parent_calc_ids=[valued.calc_id],
    )
    return PlanOut(
        portfolio_id=portfolio_id,
        target=stored.target,
        drift_threshold=stored.drift_threshold,
        goal_amount_eur=stored.goal_amount_eur,
        goal_year=stored.goal_year,
        current=current,
        drift_equity=check.drift_equity,
        drift_exceeded=check.drift_exceeded,
        calc_id=calc_id,
    )
