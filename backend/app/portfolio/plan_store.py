"""Acceso a la tabla `plan` (un plan por cartera). Lo usa `service.py`.

Las funciones reciben la sesión: la transacción la abre y la cierra quien llama.
"""

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from app.portfolio.models import Plan
from app.schemas.portfolio import TargetAllocation


@dataclass(frozen=True)
class StoredPlan:
    target: TargetAllocation
    drift_threshold: Decimal
    goal_amount_eur: Decimal | None
    goal_year: int | None


def _fraction(value: Decimal) -> Decimal:
    """La columna devuelve 8 decimales (`0.70000000`); se quitan los ceros sobrantes dejando al
    menos 2, como en el contrato (`0.70`)."""
    exponent = value.normalize().as_tuple().exponent
    places = max(2, -exponent) if isinstance(exponent, int) else 2
    return value.quantize(Decimal(1).scaleb(-places))


def get(session: Session, portfolio_id: str) -> StoredPlan | None:
    row = session.get(Plan, portfolio_id)
    if row is None:
        return None
    return StoredPlan(
        target=TargetAllocation(
            equity=_fraction(row.target_equity_pct),
            fixed_income=_fraction(row.target_fixed_income_pct),
            cash=_fraction(row.target_cash_pct),
        ),
        drift_threshold=_fraction(row.drift_threshold),
        goal_amount_eur=row.goal_amount_eur,
        goal_year=row.goal_year,
    )


def save(session: Session, portfolio_id: str, plan: StoredPlan) -> None:
    """Crea o sustituye el plan de la cartera."""
    session.merge(
        Plan(
            portfolio_id=portfolio_id,
            target_equity_pct=plan.target.equity,
            target_fixed_income_pct=plan.target.fixed_income,
            target_cash_pct=plan.target.cash,
            drift_threshold=plan.drift_threshold,
            goal_amount_eur=plan.goal_amount_eur,
            goal_year=plan.goal_year,
        )
    )
