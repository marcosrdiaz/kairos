"""Interfaz pública del gestor de cartera (diseño del MVP §4.1).

Otros módulos importan solo las funciones de *Interfaz entre módulos*. El resto las usa la API.
Reales desde T1-03: valoración, alta, catálogo, seed y reset; desde T1-04, compra y venta; desde
T1-06, DCA; desde T1-07, plan y variación de valor; desde T1-05, traspaso.
"""

from datetime import datetime
from decimal import Decimal

from app.core import clock, trace
from app.core.db import session_scope
from app.portfolio import (
    dca_flow,
    demo_adjustment,
    engine,
    errors,
    ledger,
    operations,
    plan_flow,
    repository,
    seed,
    transfers,
    value_change,
)
from app.portfolio import quotes as pricing
from app.schemas.common import Profile, SourceRef, TraceKind
from app.schemas.impact import EventImpactOut
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
    """Cartera valorada con el último precio de cada activo (RF-03). Deja traza `valuation`.

    En modo demo suma los ajustes tras un replay (D-031); su traza apunta a la del impacto.
    """
    with session_scope() as session:
        row = repository.get_portfolio(session, portfolio_id)
        if row is None:
            raise errors.portfolio_not_found(portfolio_id)
        name, profile = row.name, Profile(row.profile)
        lots = ledger.open_lots(session, portfolio_id)
        assets = repository.get_assets(session, {lot.asset_id for lot in lots})
        adjustment_rows = demo_adjustment.load(session, portfolio_id)
    adjustments = demo_adjustment.summarize(adjustment_rows, set(assets))
    quotes, sources = pricing.quotes(assets)
    valuation = engine.value_portfolio(lots, assets, quotes, adjustments.by_asset)
    calc_id = trace.record(
        TraceKind.VALUATION,
        engine.FORMULA,
        inputs={
            "portfolio_id": portfolio_id,
            "lots": [vars(lot) for lot in lots],
            "quotes": {asset_id: vars(q) for asset_id, q in quotes.items()},
            "demo_adjustments": adjustments.by_asset,
        },
        outputs={
            "total_eur": valuation.total_eur,
            "change_week_eur": valuation.change_week_eur,
            "change_week_pct": valuation.change_week_pct,
            "allocation": valuation.allocation,
            "value_eur": {p.asset_id: p.value_eur for p in valuation.positions},
        },
        sources=sources,
        parent_calc_ids=[a.calc_id for a in adjustments.by_event],
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
        demo_adjustments=adjustments.by_event,
        valued_at=clock.now(),
        calc_id=calc_id,
    )


def apply_demo_adjustment(portfolio_id: str, impact: EventImpactOut) -> None:
    """Tras un replay (lo llama `events`): la valoración suma el impacto central de cada posición,
    con la etiqueta "Estimación tras el evento" y el `calc_id` del impacto. Sustituye el ajuste
    anterior de ese evento. Solo con `DEMO_MODE=true`; fuera, no hace nada (D-031)."""
    demo_adjustment.apply(portfolio_id, impact)


def clear_demo_adjustment(portfolio_id: str, event_id: str) -> None:
    """Quita el ajuste de un evento. `events` lo llama antes de recalcular su impacto, para que
    repetir el replay no lo acumule sobre sí mismo."""
    demo_adjustment.clear(portfolio_id, event_id)


def get_plan(portfolio_id: str) -> PlanOut:
    """Plan con la asignación actual y la desviación (RF-22). Deja traza `plan`."""
    return plan_flow.get(portfolio_id, get_valued)


def list_dca_plans(portfolio_id: str) -> list[DcaPlanOut]:
    return dca_flow.list_plans(portfolio_id)


def get_value_change(portfolio_id: str, start: datetime, end: datetime) -> ValueChangeOut:
    """Valor en `start` y en `end` y flujos entre medias, por activo (para `explain_move`).
    Precios reales, sin ajustes de demo. Deja traza `move`. Ver `value_change.py`."""
    if start >= end:
        raise errors.invalid_window(start, end)
    with session_scope() as session:
        if repository.get_portfolio(session, portfolio_id) is None:
            raise errors.portfolio_not_found(portfolio_id)
        txs = ledger.transactions_until(session, portfolio_id, end)
    start_units = value_change.units_at(txs, start)
    end_units = value_change.units_at(txs, end)
    flows = value_change.flows_between(txs, start, end)
    sources: dict[tuple[str, str, str], SourceRef] = {}
    unit_eur: list[dict[str, Decimal]] = [{}, {}]
    for slot, (at, units) in enumerate(((start, start_units), (end, end_units))):
        for asset_id in sorted(units):
            unit_eur[slot][asset_id], refs = pricing.unit_eur_at(asset_id, at)
            for ref in refs:
                sources.setdefault((ref.kind, ref.ref, str(ref.as_of)), ref)
    totals = value_change.summarize(start_units, end_units, flows, unit_eur[0], unit_eur[1])
    calc_id = trace.record(
        TraceKind.MOVE,
        value_change.FORMULA,
        inputs={
            "portfolio_id": portfolio_id,
            "start": start,
            "end": end,
            "units_start": start_units,
            "units_end": end_units,
            "unit_eur_start": unit_eur[0],
            "unit_eur_end": unit_eur[1],
        },
        outputs={
            "start_value_eur": totals.start_value_eur,
            "end_value_eur": totals.end_value_eur,
            "net_flows_eur": totals.net_flows_eur,
            "by_asset": totals.by_asset,
        },
        sources=list(sources.values()),
    )
    return ValueChangeOut(
        portfolio_id=portfolio_id,
        start=start,
        end=end,
        start_value_eur=totals.start_value_eur,
        end_value_eur=totals.end_value_eur,
        net_flows_eur=totals.net_flows_eur,
        by_asset=totals.by_asset,
        calc_id=calc_id,
    )


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
    """Devuelve Laura y Javier a su estado inicial (`/demo/reset`) y borra los ajustes de demo de
    todas las carteras. Devuelve los IDs recargados."""
    demo_adjustment.clear()
    return seed.load(force=True)


# --- Traspaso (T1-05) y plan (T1-07) ---


def register_transfer(portfolio_id: str, request: TransferRequest) -> TransactionOut:
    """Traspaso fondo → fondo conservando fecha y coste (RF-06). Si alguno no es fondo, 422
    `TRANSFER_NOT_ALLOWED` con la alternativa. Ver `transfers.py`."""
    return transfers.register_transfer(portfolio_id, request, get_valued)


def update_plan(portfolio_id: str, request: PlanUpdateRequest) -> PlanOut:
    """`PUT /plan`: guarda el objetivo (debe sumar 1) y devuelve el plan evaluado."""
    return plan_flow.update(portfolio_id, request, get_valued)


# --- DCA (T1-06, RF-07). Ver `dca_flow.py` ---


def create_dca_plan(portfolio_id: str, request: DcaPlanCreateRequest) -> DcaPlanOut:
    return dca_flow.create_plan(portfolio_id, request)


def update_dca_plan(portfolio_id: str, plan_id: str, request: DcaPlanUpdateRequest) -> DcaPlanOut:
    return dca_flow.update_plan(portfolio_id, plan_id, request)


def list_dca_executions(
    portfolio_id: str, status: DcaExecutionStatus | None = None
) -> list[DcaExecutionOut]:
    """Ejecuciones DCA de la cartera (todas o solo las de `status`), la más reciente primero."""
    return dca_flow.list_executions(portfolio_id, status)


def run_dca_due() -> list[DcaExecutionOut]:
    """Job: crea las ejecuciones pendientes de los planes cuya fecha ha llegado."""
    return dca_flow.run(force=False)


def run_dca_demo() -> list[DcaExecutionOut]:
    """`POST /demo/dca/run`: crea para hoy la ejecución pendiente de cada plan activo."""
    return dca_flow.run(force=True)


def act_on_dca_execution(execution_id: str, request: DcaExecutionActionRequest) -> DcaExecutionOut:
    """Confirmar (compra `dca_buy` al precio de ahora) o saltar una aportación pendiente."""
    return dca_flow.act(execution_id, request)
