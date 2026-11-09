"""Compra y venta (RF-04, RF-05): orquesta precio, lotes (`lots.py`), traza y BD.

La aritmética es pura y está en `lots.py`; aquí se leen los lotes, se pide el precio, se deja la
traza `transaction` y se escribe en una sola transacción. Si algo falla antes de escribir (cartera,
activo, precio o participaciones), no se guarda nada.
"""

from collections.abc import Callable
from dataclasses import replace

from app.core import clock, trace
from app.core.db import session_scope
from app.portfolio import errors, ledger, lots, repository
from app.portfolio import quotes as pricing
from app.schemas.common import TraceKind
from app.schemas.portfolio import (
    LotOut,
    OperationEffect,
    OperationType,
    PortfolioOut,
    TransactionOut,
    TransactionRequest,
)


def held_lots(portfolio_id: str, asset_id: str) -> list[lots.OpenLot]:
    """Lotes abiertos del activo en FIFO. 404 si no existe la cartera o el activo."""
    with session_scope() as session:
        if repository.get_portfolio(session, portfolio_id) is None:
            raise errors.portfolio_not_found(portfolio_id)
        if asset_id not in repository.get_assets(session, [asset_id]):
            raise errors.unknown_asset(asset_id)
        return ledger.asset_lots(session, portfolio_id, asset_id)


def register_transaction(
    portfolio_id: str,
    request: TransactionRequest,
    valued: Callable[[str], PortfolioOut],
) -> TransactionOut:
    """Compra (lote nuevo) o venta (FIFO) al último precio. `valued` revalora la cartera."""
    asset_id = request.asset_id
    held = held_lots(portfolio_id, asset_id)
    quotes, sources = pricing.quotes([asset_id])
    quote = quotes[asset_id]
    trade = lots.size_trade(
        quote.price, quote.fx_rate, units=request.units, amount_eur=request.amount_eur
    )
    now = clock.now()
    is_buy = request.type == "buy"
    try:
        outcome = lots.buy(held, trade, now) if is_buy else lots.sell_fifo(held, trade)
    except lots.InsufficientUnits as exc:
        raise errors.insufficient_units(asset_id, exc.requested, exc.available) from exc
    calc_id = trace.record(
        TraceKind.TRANSACTION,
        lots.FORMULA_BUY if is_buy else lots.FORMULA_SELL,
        inputs={
            "portfolio_id": portfolio_id,
            "request": request.model_dump(mode="json", exclude_none=True),
            "quote": vars(quote),
            "lots_before": [vars(lot) for lot in held],
            "lots_consumed": [vars(lot) for lot in outcome.consumed],
        },
        outputs={
            **vars(trade),
            "realized_gain_eur": outcome.realized_gain_eur,
            "units_after": outcome.units_after,
            "avg_cost_eur_after": outcome.avg_cost_eur_after,
        },
        sources=sources,
    )
    with session_scope() as session:
        tx_id = ledger.add_transaction(
            session,
            portfolio_id,
            type=request.type,
            asset_id=asset_id,
            ts=now,
            units=trade.units,
            price=quote.price,
            price_currency=quote.currency,
            fx_rate=quote.fx_rate,
            amount_eur=trade.amount_eur,
            realized_gain_eur=outcome.realized_gain_eur,
            calc_id=calc_id,
        )
        ledger.consume_lots(session, outcome.consumed)
        created = [
            replace(lot, lot_id=ledger.add_lot(session, portfolio_id, asset_id, lot, tx_id))
            for lot in outcome.created
        ]
    return TransactionOut(
        transaction_id=tx_id,
        type=OperationType(request.type),
        asset_id=asset_id,
        units=trade.units,
        price=quote.price,
        price_currency=quote.currency,
        price_at=quote.price_at,
        fx_rate=quote.fx_rate,
        amount_eur=trade.amount_eur,
        effect=OperationEffect(
            units_after=outcome.units_after,
            avg_cost_eur_after=outcome.avg_cost_eur_after,
            realized_gain_eur=outcome.realized_gain_eur,
            lots_consumed=[LotOut(**vars(lot)) for lot in outcome.consumed],
            lots_created=[LotOut(**vars(lot)) for lot in created],
        ),
        portfolio=valued(portfolio_id),
        calc_id=calc_id,
    )
