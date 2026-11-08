"""Acceso a las tablas de `impact/` (`factor_beta`, `event_impact`). Solo aquí se abren sesiones."""

from collections.abc import Iterable, Sequence

from sqlalchemy import delete, select

from app.core.db import session_scope
from app.impact.betas import BetaEstimate
from app.impact.models import FactorBeta
from app.schemas.common import Factor


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
