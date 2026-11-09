"""Interfaz pública del gestor de cartera (diseño del MVP §4.1).

Otros módulos importan solo las funciones de *Interfaz entre módulos*. El resto las usa la API.
Reales desde T1-03: valoración, alta, catálogo, seed y reset; desde T1-04, compra y venta.
Lo demás aún delega en `mock.py`; T1-05 a T1-07 lo cambian sin cambiar las firmas.
"""

from datetime import datetime

from app.core import clock, trace
from app.core.db import session_scope
from app.portfolio import engine, errors, ledger, mock, operations, repository, seed
from app.portfolio import quotes as pricing
from app.schemas.common import Profile, TraceKind
from app.schemas.portfolio import (
    AssetOut,
    DcaExecutionActionRequest,
    DcaExecutionOut,
    DcaExecutionStatus,
    DcaPlanCreateRequest,
    DcaPlanOut,
    DcaPlanUpdateRequest,
    PlanOut,
    PlanUpdateRequest,
    PortfolioOut,
    PortfolioSummaryOut,
    PositionsInitRequest,
    TransactionOut,
    TransactionRequest,
    TransferRequest,
    ValueChangeOut,
)

LOOKUP_LIMIT = 20


# --- Interfaz entre módulos (§4.1) ---


def get_valued(portfolio_id: str) -> PortfolioOut:
    """Cartera valorada con el último precio de cada activo (RF-03). Deja traza `valuation`."""
    with session_scope() as session:
        row = repository.get_portfolio(session, portfolio_id)
        if row is None:
            raise errors.portfolio_not_found(portfolio_id)
        name, profile = row.name, Profile(row.profile)
        lots = ledger.open_lots(session, portfolio_id)
        assets = repository.get_assets(session, {lot.asset_id for lot in lots})
    quotes, sources = pricing.quotes(assets)
    valuation = engine.value_portfolio(lots, assets, quotes)
    calc_id = trace.record(
        TraceKind.VALUATION,
        engine.FORMULA,
        inputs={
            "portfolio_id": portfolio_id,
            "lots": [vars(lot) for lot in lots],
            "quotes": {asset_id: vars(q) for asset_id, q in quotes.items()},
        },
        outputs={
            "total_eur": valuation.total_eur,
            "change_week_eur": valuation.change_week_eur,
            "change_week_pct": valuation.change_week_pct,
            "allocation": valuation.allocation,
            "value_eur": {p.asset_id: p.value_eur for p in valuation.positions},
        },
        sources=sources,
    )
    return PortfolioOut(
        id=portfolio_id,
        name=name,
        profile=profile,
        total_eur=valuation.total_eur,
        change_week_eur=valuation.change_week_eur,
        change_week_pct=valuation.change_week_pct,
        allocation=valuation.allocation,
        positions=valuation.positions,
        demo_adjustments=[],
        valued_at=clock.now(),
        calc_id=calc_id,
    )


def get_plan(portfolio_id: str) -> PlanOut:
    return mock.get_plan(portfolio_id)


def list_dca_plans(portfolio_id: str) -> list[DcaPlanOut]:
    return mock.list_dca_plans(portfolio_id)


def get_value_change(portfolio_id: str, start: datetime, end: datetime) -> ValueChangeOut:
    return mock.get_value_change(portfolio_id, start, end)


def list_portfolio_ids() -> list[str]:
    """Primero las del seed (Laura, Javier); después el resto, por orden alfabético."""
    with session_scope() as session:
        ids = repository.list_portfolio_ids(session)
    order = {pid: n for n, pid in enumerate(seed.SEED_PORTFOLIOS)}
    return sorted(ids, key=lambda pid: (order.get(pid, len(order)), pid))


def ensure_exists(portfolio_id: str) -> None:
    """404 `NOT_FOUND` si la cartera no existe. No valora: no necesita precios."""
    with session_scope() as session:
        if repository.get_portfolio(session, portfolio_id) is None:
            raise errors.portfolio_not_found(portfolio_id)


# --- Para la API de cartera ---


def list_portfolios() -> list[PortfolioSummaryOut]:
    ids = list_portfolio_ids()
    with session_scope() as session:
        rows = [repository.get_portfolio(session, pid) for pid in ids]
        return [
            PortfolioSummaryOut(id=r.id, name=r.name, profile=Profile(r.profile))
            for r in rows
            if r is not None
        ]


def lookup_assets(query: str) -> list[AssetOut]:
    """Autocompletar del alta (`GET /assets/lookup?q=`): por ISIN, ticker o nombre."""
    with session_scope() as session:
        return repository.search_assets(session, query, LOOKUP_LIMIT)


def register_transaction(portfolio_id: str, request: TransactionRequest) -> TransactionOut:
    """Compra (lote nuevo) o venta (FIFO) al último precio (RF-04, RF-05). Ver `operations.py`."""
    return operations.register_transaction(portfolio_id, request, get_valued)


def init_positions(portfolio_id: str, request: PositionsInitRequest) -> PortfolioOut:
    """Alta (`initial`): un lote por línea. Si un activo no existe o no tiene precio, no guarda
    nada (404 `NOT_FOUND` o 503 `PRICE_UNAVAILABLE`)."""
    asset_ids = [line.asset_id for line in request.positions]
    with session_scope() as session:
        if repository.get_portfolio(session, portfolio_id) is None:
            raise errors.portfolio_not_found(portfolio_id)
        known = repository.get_assets(session, asset_ids)
    for asset_id in asset_ids:
        if asset_id not in known:
            raise errors.unknown_asset(asset_id)
    pricing.quotes(set(asset_ids))  # PRICE_UNAVAILABLE antes de escribir nada
    now = clock.now()
    with session_scope() as session:
        for line in request.positions:
            ledger.add_initial_lot(
                session,
                portfolio_id,
                line.asset_id,
                line.acquired_at or now,
                line.units,
                line.avg_cost_eur,
            )
    return get_valued(portfolio_id)


# --- Seed y demo ---


def load_seed(force: bool = False) -> list[str]:
    """Carga `data/seed` (idempotente; con `force`, vuelve al estado inicial). La usa
    `scripts/seed_db.py` en cada arranque de Compose."""
    return seed.load(force=force)


def reset_demo() -> list[str]:
    """Devuelve Laura y Javier a su estado inicial (`/demo/reset`). Devuelve los IDs recargados."""
    return seed.load(force=True)


# --- Aún sobre el mock (T1-05 a T1-07) ---


def register_transfer(portfolio_id: str, request: TransferRequest) -> TransactionOut:
    return mock.register_transfer(portfolio_id, request)


def update_plan(portfolio_id: str, request: PlanUpdateRequest) -> PlanOut:
    plan = mock.get_plan(portfolio_id)
    return plan.model_copy(update=request.model_dump(exclude_unset=True))


def create_dca_plan(portfolio_id: str, request: DcaPlanCreateRequest) -> DcaPlanOut:
    plan = mock.list_dca_plans(portfolio_id)[0]
    return plan.model_copy(update=request.model_dump(exclude_unset=True))


def update_dca_plan(portfolio_id: str, plan_id: str, request: DcaPlanUpdateRequest) -> DcaPlanOut:
    plan = mock.list_dca_plans(portfolio_id)[0]
    return plan.model_copy(update={"id": plan_id, **request.model_dump(exclude_unset=True)})


def act_on_dca_execution(execution_id: str, request: DcaExecutionActionRequest) -> DcaExecutionOut:
    status = (
        DcaExecutionStatus.CONFIRMED if request.action == "confirm" else DcaExecutionStatus.SKIPPED
    )
    return mock.get_dca_execution(execution_id).model_copy(update={"status": status})
