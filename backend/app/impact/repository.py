"""Acceso a las tablas de `impact/` (`factor_beta`, `event_impact`). Solo aquí se abren sesiones."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import delete, select

from app.core import clock
from app.core.db import session_scope
from app.impact.betas import BetaEstimate
from app.impact.models import EventImpact, FactorBeta
from app.schemas.agents import ExplanationStatus
from app.schemas.common import Factor
from app.schemas.impact import EventImpactOut


@dataclass(frozen=True)
class StoredImpact:
    """Lo que cambia tras calcular. El resto del resultado está en la traza `calc_id`."""

    calc_id: str
    explanation: str | None
    explanation_status: str


def save_event_impact(impact: EventImpactOut) -> None:
    """Guarda el impacto. Si el evento se reinyecta, sustituye el anterior."""
    with session_scope() as session:
        session.merge(
            EventImpact(
                event_id=impact.event_id,
                portfolio_id=impact.portfolio_id,
                impact_eur=impact.impact_eur,
                low_eur=impact.low_eur,
                high_eur=impact.high_eur,
                impact_pct=impact.impact_pct,
                confidence=impact.confidence.value,
                polarity=impact.polarity.value,
                breakdown=[a.model_dump(mode="json") for a in impact.breakdown],
                explanation=impact.explanation,
                explanation_status=impact.explanation_status.value,
                calc_id=impact.calc_id,
                created_at=clock.now(),
            )
        )


def delete_event_impacts() -> None:
    with session_scope() as session:
        session.execute(delete(EventImpact))


def set_explanation(event_id: str, portfolio_id: str, text: str, status: ExplanationStatus) -> bool:
    """`False` si no hay impacto guardado para ese evento y esa cartera."""
    with session_scope() as session:
        row = session.get(EventImpact, (event_id, portfolio_id))
        if row is None:
            return False
        row.explanation = text
        row.explanation_status = status.value
        return True


def list_event_impacts(portfolio_id: str, since: datetime) -> list[StoredImpact]:
    """Impactos calculados desde `since`, del más reciente al más antiguo."""
    with session_scope() as session:
        rows = session.scalars(
            select(EventImpact)
            .where(EventImpact.portfolio_id == portfolio_id, EventImpact.created_at >= since)
            .order_by(EventImpact.created_at.desc(), EventImpact.event_id)
        ).all()
        return [StoredImpact(r.calc_id, r.explanation, r.explanation_status) for r in rows]


def replace_betas(estimates: Sequence[BetaEstimate], clear: Iterable[str] = ()) -> int:
    """Sustituye las betas de los activos de `estimates` y de `clear`. Idempotente.

    `clear` son activos cuyas betas antiguas se borran aunque ahora no tengan estimación (p. ej.
    porque sus datos ya no bastan): así no quedan sensibilidades obsoletas en `factor_beta`.
    """
    asset_ids = {e.asset_id for e in estimates} | set(clear)
    if not asset_ids:
        return 0
    with session_scope() as session:
        session.execute(delete(FactorBeta).where(FactorBeta.asset_id.in_(asset_ids)))
        session.add_all(
            FactorBeta(
                asset_id=e.asset_id,
                factor=e.factor.value,
                beta=e.beta,
                std_err=e.std_err,
                r2=e.r2,
                n_obs=e.n_obs,
                window_start=e.window_start,
                window_end=e.window_end,
            )
            for e in estimates
        )
    return len(estimates)


def get_betas(asset_ids: Iterable[str]) -> list[BetaEstimate]:
    """Betas guardadas de esos activos, ordenadas por activo y factor."""
    ids = list(asset_ids)
    with session_scope() as session:
        rows = session.scalars(
            select(FactorBeta)
            .where(FactorBeta.asset_id.in_(ids))
            .order_by(FactorBeta.asset_id, FactorBeta.factor)
        ).all()
        return [
            BetaEstimate(
                asset_id=r.asset_id,
                factor=Factor(r.factor),
                beta=r.beta,
                std_err=r.std_err,
                r2=r.r2,
                n_obs=r.n_obs,
                window_start=r.window_start,
                window_end=r.window_end,
            )
            for r in rows
        ]
