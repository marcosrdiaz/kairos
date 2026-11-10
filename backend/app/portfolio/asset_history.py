"""Evolución de una posición (T2-23, `AssetHistoryOut`).

Las reglas de `history.py` (D-057, T2-18) con las operaciones de un solo activo:

- Días: los de `history.sample_days`, desde la primera operación de este activo, y solo los que
  tienen cierre de este activo (los de valor fijo, todos).
- Participaciones del día `d` = operaciones del activo con `ts` hasta el final de `d`. Con 0
  (posición ya vendida), el valor es 0 y el precio sigue saliendo.
- `price` = último cierre no posterior a `d` (como mucho 10 días antes), en la divisa del activo.
  Valor = participaciones × `price` × fx de `d`, a céntimos. Sin precio o sin fx, el día se omite.
- Flujos = solo las operaciones de este activo. Precios reales, sin ajustes de demo (D-031).
"""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal

from app.core import clock, trace
from app.core.db import session_scope
from app.core.errors import AppError, ErrorCode
from app.portfolio import errors, ledger, repository, value_change
from app.portfolio.history import (
    CENT,
    _Prices,
    build_points,
    end_of,
    last_close,
    sample_days,
)
from app.portfolio.value_change import TxIn
from app.schemas.common import TraceKind
from app.schemas.history import AssetHistoryOut, AssetHistoryPoint, HistoryPeriod

FORMULA = (
    "V(d) = units(d) × close(≤d, máx. 10 días) × fx(d) (a céntimos); "
    "units(d) = Σ operaciones del activo con ts ≤ fin de d; se omiten los días sin precio; "
    "net_flows = Σ ±amount_eur del activo entre el fin del primer día y el fin del último"
)


@dataclass(frozen=True)
class _Day:
    day: date
    price: Decimal
    units: Decimal
    value_eur: Decimal


class _AssetPrices(_Prices):
    """Los precios de `history.py` para un activo, con el cierre en su divisa."""

    def __init__(self, asset_id: str, start: date, end: date) -> None:
        super().__init__({asset_id}, start, end)
        self.asset_id = asset_id

    @property
    def currency(self) -> str | None:
        return self._currency.get(self.asset_id)

    def close(self, day: date) -> Decimal | None:
        return last_close(self._closes.get(self.asset_id, []), day)


def _load(portfolio_id: str, asset_id: str, today: date) -> tuple[list[TxIn], str]:
    """Operaciones del activo en la cartera y su nombre. 404 si la cartera no existe o nunca
    tuvo el activo."""
    with session_scope() as session:
        if repository.get_portfolio(session, portfolio_id) is None:
            raise errors.portfolio_not_found(portfolio_id)
        txs = [
            tx
            for tx in ledger.transactions_until(session, portfolio_id, end_of(today))
            if tx.asset_id == asset_id
        ]
        asset = repository.get_assets(session, [asset_id]).get(asset_id)
    if not txs or asset is None:
        raise AppError(
            ErrorCode.NOT_FOUND,
            "Esta cartera no ha tenido nunca ese activo.",
            details={"portfolio_id": portfolio_id, "asset_id": asset_id},
        )
    return txs, asset.name


def _no_prices(portfolio_id: str, asset_id: str, period: HistoryPeriod) -> AppError:
    return AppError(
        ErrorCode.PRICE_UNAVAILABLE,
        "No hay precios para valorar esta posición en ese periodo.",
        details={"portfolio_id": portfolio_id, "asset_id": asset_id, "period": period.value},
    )


def _value_days(quotes: _AssetPrices, days: list[date], txs: list[TxIn]) -> list[_Day]:
    out: list[_Day] = []
    for day in days:
        price, unit_eur = quotes.close(day), quotes.unit_eur(quotes.asset_id, day)
        if price is None or unit_eur is None:
            continue
        units = value_change.units_at(txs, end_of(day)).get(quotes.asset_id, Decimal(0))
        value = (units * unit_eur).quantize(CENT, rounding=ROUND_HALF_EVEN)
        out.append(_Day(day, price, units, value))
    return out


def get_asset_history(portfolio_id: str, asset_id: str, period: HistoryPeriod) -> AssetHistoryOut:
    """Valor de una posición en cada día del periodo. Deja traza `valuation`."""
    today = clock.now().date()
    txs, name = _load(portfolio_id, asset_id, today)
    first_day = min(tx.ts for tx in txs).date()
    quotes = _AssetPrices(asset_id, first_day, today)
    sampled = sample_days(quotes.last_market_day(today), period, first_day)
    days = [d for d in sampled if quotes.is_market_day(d)]
    valued = _value_days(quotes, days, txs)
    if not valued or quotes.currency is None:
        raise _no_prices(portfolio_id, asset_id, period)
    base = build_points([(v.day, v.value_eur) for v in valued], txs)
    points = [
        AssetHistoryPoint(**p.model_dump(), price=v.price, units=v.units)
        for p, v in zip(base, valued, strict=True)
    ]
    first, last = valued[0].day, valued[-1].day
    flows = value_change.flows_between(txs, end_of(first), end_of(last))
    net_flows = sum(flows.values(), Decimal(0)).quantize(CENT, rounding=ROUND_HALF_EVEN)
    sources = list(quotes.sources.values())
    calc_id = trace.record(
        TraceKind.VALUATION,
        FORMULA,
        inputs={
            "portfolio_id": portfolio_id,
            "asset_id": asset_id,
            "period": period.value,
            "days": [d.isoformat() for d in days],
            "transactions": [
                {"ts": t.ts, "type": t.type, "units": t.units, "amount_eur": t.amount_eur}
                for t in txs
            ],
        },
        outputs={
            "points": [[v.day.isoformat(), v.price, v.units, v.value_eur] for v in valued],
            "start_value_eur": points[0].value_eur,
            "end_value_eur": points[-1].value_eur,
            "net_flows_eur": net_flows,
        },
        sources=sources,
    )
    return AssetHistoryOut(
        portfolio_id=portfolio_id,
        asset_id=asset_id,
        name=name,
        currency=quotes.currency,
        period=period,
        points=points,
        start_value_eur=points[0].value_eur,
        end_value_eur=points[-1].value_eur,
        net_flows_eur=net_flows,
        calc_id=calc_id,
        sources=sources,
    )
