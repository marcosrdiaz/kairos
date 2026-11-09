"""Traspaso fondo → fondo (RF-06): lotes que conservan fecha y coste, y error con alternativa.

Reglas (`SPEC.md` §7):

- Solo entre fondos (`asset_type == fund`). Si no, 422 `TRANSFER_NOT_ALLOWED` con la alternativa
  (vender y comprar; la venta tributa) y la plusvalía estimada de esa venta, con su traza.
- El origen se valora como una venta (`lots.size_trade` y `lots.sell_fifo`), sin plusvalía.
- Cada lote consumido abre un lote en el destino con la **misma `acquired_at`**,
  `units = units_consumidas × unit_eur_origen / unit_eur_destino` y
  `coste = units_consumidas × coste_origen / units` (8 decimales, HALF_EVEN), que conserva el
  coste total.
- En el libro: `transfer_out` en el origen y `transfer_in` en el destino, por el mismo importe
  (`linked_tx_id` del de entrada apunta al de salida), con una sola traza `transfer`.

`plan_lots` es pura; `register_transfer` lee, pide precios, deja la traza y escribe en una sola
transacción. Si algo falla antes de escribir, no se guarda nada.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from decimal import ROUND_HALF_EVEN, Decimal

from app.core import clock, trace
from app.core.db import session_scope
from app.core.errors import AppError, ErrorCode
from app.portfolio import errors, ledger, lots, repository
from app.portfolio import quotes as pricing
from app.portfolio.engine import AssetIn
from app.schemas.common import AssetType, TraceKind
from app.schemas.portfolio import (
    LotOut,
    OperationEffect,
    OperationType,
    PortfolioOut,
    TransactionOut,
    TransferRequest,
)

FORMULA = (
    "unit_eur = price × fx; origen como venta FIFO (units = amount_eur / unit_eur o al revés); "
    "por lote consumido: units_destino = units × unit_eur_origen / unit_eur_destino, "
    "coste_destino = units × coste_origen / units_destino, misma fecha de adquisición"
)
FORMULA_ESTIMATE = (
    "plusvalía estimada de vender en vez de traspasar: "
    "amount_eur − Σ units_lote × coste_lote (FIFO)"
)
NOT_ALLOWED_MESSAGE = (
    "Los ETF y las acciones no admiten traspaso sin tributar. "
    "Puedes registrar una venta y una compra; la venta tributa."
)
_UNIT = Decimal("0.00000001")


@dataclass(frozen=True)
class TransferPlan:
    trade: lots.Trade
    """Participaciones e importe que salen del origen."""
    origin: lots.Outcome
    """Efecto sobre el origen (`realized_gain_eur` se ignora: el traspaso no tributa)."""
    created: list[lots.OpenLot]
    """Lotes del destino, sin `lot_id`, en el orden de los consumidos."""
    to_units: Decimal


def _q(value: Decimal) -> Decimal:
    return value.quantize(_UNIT, rounding=ROUND_HALF_EVEN)


def plan_lots(
    held: Sequence[lots.OpenLot], trade: lots.Trade, to_unit_eur: Decimal
) -> TransferPlan:
    """Consume `trade.units` del origen por FIFO y abre los lotes equivalentes en el destino.

    Lanza `lots.InsufficientUnits` si no hay bastantes participaciones. Un trozo cuyo equivalente
    redondea a 0 participaciones no abre lote (su coste es < 0,000001 €)."""
    origin = lots.sell_fifo(held, trade)
    to_unit = _q(to_unit_eur)
    created: list[lots.OpenLot] = []
    for part in origin.consumed:
        units = _q(part.units * trade.unit_eur / to_unit)
        if units > 0:
            cost = _q(part.units * part.cost_eur_per_unit / units)
            created.append(lots.OpenLot("", part.acquired_at, units, cost))
    to_units = sum((lot.units for lot in created), lots.ZERO)
    return TransferPlan(trade, origin, created, to_units)


def _assets(portfolio_id: str, request: TransferRequest) -> tuple[AssetIn, AssetIn]:
    with session_scope() as session:
        if repository.get_portfolio(session, portfolio_id) is None:
            raise errors.portfolio_not_found(portfolio_id)
        assets = repository.get_assets(session, [request.from_asset_id, request.to_asset_id])
    for asset_id in (request.from_asset_id, request.to_asset_id):
        if asset_id not in assets:
            raise errors.unknown_asset(asset_id)
    return assets[request.from_asset_id], assets[request.to_asset_id]


def _not_allowed(
    portfolio_id: str, request: TransferRequest, origin: AssetIn, destination: AssetIn
) -> AppError:
    """422 con la plusvalía que tendría vender en vez de traspasar (o `None` si no se puede)."""
    gain, calc_id = _estimate_sale_gain(portfolio_id, request)
    return AppError(
        ErrorCode.TRANSFER_NOT_ALLOWED,
        NOT_ALLOWED_MESSAGE,
        details={
            "from_asset_type": origin.asset_type.value,
            "to_asset_type": destination.asset_type.value,
            "alternative": "sell_and_buy",
            "estimated_gain_eur": None if gain is None else str(gain),
            "calc_id": calc_id,
        },
    )


def _estimate_sale_gain(
    portfolio_id: str, request: TransferRequest
) -> tuple[Decimal | None, str | None]:
    asset_id = request.from_asset_id
    try:
        with session_scope() as session:
            held = ledger.asset_lots(session, portfolio_id, asset_id)
        quotes, sources = pricing.quotes([asset_id])
        quote = quotes[asset_id]
        trade = lots.size_trade(
            quote.price, quote.fx_rate, units=request.units, amount_eur=request.amount_eur
        )
        sale = lots.sell_fifo(held, trade)
    except (AppError, lots.InsufficientUnits):
        return None, None
    calc_id = trace.record(
        TraceKind.TRANSFER,
        FORMULA_ESTIMATE,
        inputs={
            "portfolio_id": portfolio_id,
            "request": request.model_dump(mode="json", exclude_none=True),
            "quote": vars(quote),
            "lots_consumed": [vars(lot) for lot in sale.consumed],
        },
        outputs={**vars(trade), "estimated_gain_eur": sale.realized_gain_eur},
        sources=sources,
    )
    return sale.realized_gain_eur, calc_id


def register_transfer(
    portfolio_id: str,
    request: TransferRequest,
    valued: Callable[[str], PortfolioOut],
) -> TransactionOut:
    """Traspasa del fondo `from_asset_id` al `to_asset_id` al último VL. `valued` revalora."""
    from_id, to_id = request.from_asset_id, request.to_asset_id
    if from_id == to_id:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "El fondo de origen y el de destino son el mismo.",
            details={"from_asset_id": from_id, "to_asset_id": to_id},
        )
    origin, destination = _assets(portfolio_id, request)
    if origin.asset_type is not AssetType.FUND or destination.asset_type is not AssetType.FUND:
        raise _not_allowed(portfolio_id, request, origin, destination)
    with session_scope() as session:
        held = ledger.asset_lots(session, portfolio_id, from_id)
    quotes, sources = pricing.quotes([from_id, to_id])
    q_from, q_to = quotes[from_id], quotes[to_id]
    trade = lots.size_trade(
        q_from.price, q_from.fx_rate, units=request.units, amount_eur=request.amount_eur
    )
    try:
        plan = plan_lots(held, trade, q_to.price * q_to.fx_rate)
    except lots.InsufficientUnits as exc:
        raise errors.insufficient_units(from_id, exc.requested, exc.available) from exc
    calc_id = trace.record(
        TraceKind.TRANSFER,
        FORMULA,
        inputs={
            "portfolio_id": portfolio_id,
            "request": request.model_dump(mode="json", exclude_none=True),
            "quote_from": vars(q_from),
            "quote_to": vars(q_to),
            "lots_before": [vars(lot) for lot in held],
            "lots_consumed": [vars(lot) for lot in plan.origin.consumed],
        },
        outputs={
            **vars(trade),
            "to_units": plan.to_units,
            "lots_created": [vars(lot) for lot in plan.created],
            "units_after": plan.origin.units_after,
            "avg_cost_eur_after": plan.origin.avg_cost_eur_after,
        },
        sources=sources,
    )
    now = clock.now()
    with session_scope() as session:
        out_id = ledger.add_transaction(
            session,
            portfolio_id,
            type="transfer_out",
            asset_id=from_id,
            ts=now,
            units=trade.units,
            price=q_from.price,
            price_currency=q_from.currency,
            fx_rate=q_from.fx_rate,
            amount_eur=trade.amount_eur,
            calc_id=calc_id,
        )
        in_id = ledger.add_transaction(
            session,
            portfolio_id,
            type="transfer_in",
            asset_id=to_id,
            ts=now,
            units=plan.to_units,
            price=q_to.price,
            price_currency=q_to.currency,
            fx_rate=q_to.fx_rate,
            amount_eur=trade.amount_eur,
            linked_tx_id=out_id,
            calc_id=calc_id,
        )
        ledger.consume_lots(session, plan.origin.consumed)
        created = [
            replace(lot, lot_id=ledger.add_lot(session, portfolio_id, to_id, lot, in_id))
            for lot in plan.created
        ]
    return TransactionOut(
        transaction_id=out_id,
        type=OperationType.TRANSFER,
        asset_id=from_id,
        to_asset_id=to_id,
        units=trade.units,
        price=q_from.price,
        price_currency=q_from.currency,
        price_at=q_from.price_at,
        fx_rate=q_from.fx_rate,
        amount_eur=trade.amount_eur,
        effect=OperationEffect(
            units_after=plan.origin.units_after,
            avg_cost_eur_after=plan.origin.avg_cost_eur_after,
            realized_gain_eur=None,
            lots_consumed=[LotOut(**vars(lot)) for lot in plan.origin.consumed],
            lots_created=[LotOut(**vars(lot)) for lot in created],
        ),
        portfolio=valued(portfolio_id),
        calc_id=calc_id,
    )
