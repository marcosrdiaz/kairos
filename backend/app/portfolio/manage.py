"""Crear, renombrar y borrar carteras (T4-10). Lo expone `portfolio/service.py`.

Sin login: cada cartera es independiente y nunca se suman cifras entre carteras. Los ids los
genera el backend (`pf_` + hex). `profile` (obsoleto) se guarda siempre a juego con
`risk_profile`, porque el resto de módulos todavía lo leen.
"""

from app.core import clock
from app.core.db import session_scope
from app.portfolio import errors, ledger, repository
from app.portfolio.models import Portfolio
from app.schemas.common import PortfolioKind, Profile, RiskProfile
from app.schemas.portfolio import PortfolioSummaryOut
from app.schemas.portfolio_manage import (
    LEGACY_PROFILE,
    PortfolioCreateRequest,
    PortfolioUpdateRequest,
)

BASE_CURRENCY = "EUR"
_RISK_FROM_PROFILE = {legacy: risk for risk, legacy in LEGACY_PROFILE.items()}


def risk_from_profile(profile: Profile) -> RiskProfile:
    """`dinamico` → `agresivo`; el resto se llama igual. Para el seed y las carteras antiguas."""
    return _RISK_FROM_PROFILE[profile]


def summary(row: Portfolio) -> PortfolioSummaryOut:
    profile = Profile(row.profile)
    risk = RiskProfile(row.risk_profile) if row.risk_profile else risk_from_profile(profile)
    return PortfolioSummaryOut(
        id=row.id,
        name=row.name,
        profile=profile,
        kind=PortfolioKind(row.kind) if row.kind else PortfolioKind.PERSONAL,
        risk_profile=risk,
    )


def create(request: PortfolioCreateRequest) -> PortfolioSummaryOut:
    """Cartera vacía: sin posiciones, plan ni DCA."""
    portfolio_id = repository.new_id("pf")
    with session_scope() as session:
        repository.upsert_portfolio(
            session,
            portfolio_id,
            request.name,
            LEGACY_PROFILE[request.risk_profile].value,
            BASE_CURRENCY,
            clock.now(),
            kind=request.kind.value,
            risk_profile=request.risk_profile.value,
        )
        row = repository.get_portfolio(session, portfolio_id)
        assert row is not None
        return summary(row)


def update(portfolio_id: str, request: PortfolioUpdateRequest) -> PortfolioSummaryOut:
    """Cambia solo lo que llega en la petición. 404 si la cartera no existe."""
    with session_scope() as session:
        row = repository.get_portfolio(session, portfolio_id)
        if row is None:
            raise errors.portfolio_not_found(portfolio_id)
        current = summary(row)
        risk = request.risk_profile or current.risk_profile or RiskProfile.MODERADO
        kind = request.kind or current.kind or PortfolioKind.PERSONAL
        repository.upsert_portfolio(
            session,
            portfolio_id,
            request.name or current.name,
            LEGACY_PROFILE[risk].value,
            row.base_currency,
            row.created_at,
            kind=kind.value,
            risk_profile=risk.value,
        )
        return summary(row)


def held_asset_ids() -> list[str]:
    """Activos con participaciones vivas en alguna cartera, sin repetir y ordenados (T4-02: qué
    cierres guarda la actualización diaria). Solo dice qué activos son, nunca suma carteras."""
    with session_scope() as session:
        held = {
            lot.asset_id
            for portfolio_id in repository.list_portfolio_ids(session)
            for lot in ledger.open_lots(session, portfolio_id)
        }
    return sorted(held)


def delete(portfolio_id: str) -> None:
    """Borra la cartera y todo lo suyo (operaciones, lotes, plan, DCA, ajustes de demo, avisos e
    impactos). No toca las demás. 404 si no existe."""
    with session_scope() as session:
        if repository.get_portfolio(session, portfolio_id) is None:
            raise errors.portfolio_not_found(portfolio_id)
        repository.delete_portfolio(session, portfolio_id)
