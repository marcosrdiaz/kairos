"""Evolución del valor de una cartera (T2-18, `PortfolioHistoryOut`).

Reglas (las de `value_change.py`, D-057, aplicadas a una serie de días):

- Días: hábiles (lunes a viernes) desde el mismo día de hace 1 semana o 1, 6 o 12 meses hasta el
  último día con algún cierre de mercado no posterior a hoy. Con `max`, uno por semana hacia
  atrás desde ese último día. Nunca antes de la primera operación de la cartera. Solo se dibujan
  los días con algún cierre de mercado (festivos y días aún sin cierre fuera); los activos de
  valor fijo no cuentan, porque tienen un punto por día natural.
- Participaciones del día `d` = operaciones con `ts` hasta el final de `d` (23:59:59 UTC).
- Valor de un activo en `d` = participaciones × último cierre no posterior a `d` (como mucho 10
  días antes) × fx de `d`, a céntimos. Si falta el precio de algún activo, el día se omite.
- Flujos del periodo = operaciones entre el final del primer día y el final del último.
- Precios reales, sin los ajustes de demo del replay (D-031).
"""

import bisect
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, time, timedelta
from decimal import ROUND_HALF_EVEN, Decimal

from app.core import clock, trace
from app.core.db import session_scope
from app.core.errors import AppError, ErrorCode
from app.portfolio import errors, ledger, repository, value_change
from app.portfolio.value_change import TxIn
from app.prices import service as prices
from app.schemas.common import SourceRef, TraceKind
from app.schemas.history import HistoryPeriod, PortfolioHistoryOut, PortfolioHistoryPoint

CENT = Decimal("0.01")
MAX_PRICE_AGE = timedelta(days=10)
WEEK = timedelta(days=7)
MONTHS = {
    HistoryPeriod.ONE_MONTH: 1,
    HistoryPeriod.SIX_MONTHS: 6,
    HistoryPeriod.ONE_YEAR: 12,
}

FORMULA = (
    "V(d) = Σ_i units_i(d) × close_i(≤d, máx. 10 días) × fx_i(d) (a céntimos por activo); "
    "units_i(d) = Σ operaciones con ts ≤ fin de d; se omiten los días sin precio de algún activo; "
    "net_flows = Σ ±amount_eur entre el fin del primer día y el fin del último"
)

Series = Sequence[tuple[date, Decimal]]


# --- Funciones puras ---


def _months_back(day: date, months: int) -> date:
    month_index = day.year * 12 + day.month - 1 - months
    year, month = divmod(month_index, 12)
    for candidate in range(day.day, 0, -1):  # 31 de marzo − 1 mes → 28/29 de febrero
        try:
            return date(year, month + 1, candidate)
        except ValueError:
            continue
    raise ValueError(f"Fecha imposible: {day} − {months} meses")


def _last_weekday(day: date) -> date:
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day


def sample_days(today: date, period: HistoryPeriod, first: date) -> list[date]:
    """Días de la serie, en orden. `first` es el día de la primera operación de la cartera."""
    end = _last_weekday(today)
    if period is HistoryPeriod.MAX:
        days: list[date] = []
        day = end
        while day >= first:
            days.append(day)
            day -= timedelta(days=7)
        return days[::-1]
    back = end - WEEK if period is HistoryPeriod.ONE_WEEK else _months_back(end, MONTHS[period])
    start = max(back, first)
    count = (end - start).days + 1
    every = (start + timedelta(days=n) for n in range(count))
    return [d for d in every if d.weekday() < 5]


def last_close(series: Series, day: date) -> Decimal | None:
    """Último valor de `series` (ordenada) no posterior a `day` y como mucho 10 días antes."""
    index = bisect.bisect_right([d for d, _ in series], day) - 1
    if index < 0:
        return None
    close_day, value = series[index]
    return value if day - close_day <= MAX_PRICE_AGE else None


def day_value(
    units: Mapping[str, Decimal], unit_eur: Mapping[str, Decimal | None]
) -> Decimal | None:
    """Σ participaciones × valor unitario en euros, a céntimos por activo. `None` si no hay
    posiciones o si falta el valor de alguna."""
    if not units:
        return None
    total = Decimal(0).quantize(CENT)
    for asset_id, held in units.items():
        price = unit_eur.get(asset_id)
        if price is None:
            return None
        total += (held * price).quantize(CENT, rounding=ROUND_HALF_EVEN)
    return total


def end_of(day: date) -> datetime:
    return datetime.combine(day, time(23, 59, 59), tzinfo=UTC)


# --- Precios: una lectura por activo y un fx por divisa y día ---


class _Prices:
    def __init__(self, asset_ids: set[str], start: date, end: date) -> None:
        self._closes: dict[str, list[tuple[date, Decimal]]] = {}
        self._currency: dict[str, str] = {}
        self._fx: dict[tuple[str, date], Decimal | None] = {}
        self.sources: dict[tuple[str, str], SourceRef] = {}
        self._market_days: set[date] = set()
        for asset_id in sorted(asset_ids):
            rows = prices.history(asset_id, start - MAX_PRICE_AGE, end)
            self._closes[asset_id] = [(r.price_at.date(), r.price) for r in rows]
            if rows:
                self._currency[asset_id] = rows[-1].currency
                self.sources.setdefault((rows[-1].source.kind, asset_id), rows[-1].source)
            if prices.has_market_prices(asset_id):
                self._market_days.update(r.price_at.date() for r in rows)

    def last_market_day(self, today: date) -> date:
        """Último día con algún cierre de mercado; `today` si solo hay activos de valor fijo."""
        known = [d for d in self._market_days if d <= today]
        return max(known) if known else today

    def is_market_day(self, day: date) -> bool:
        """Días con algún cierre de mercado: los demás no se dibujan (nada de rellenar)."""
        return not self._market_days or day in self._market_days

    def unit_eur(self, asset_id: str, day: date) -> Decimal | None:
        close = last_close(self._closes.get(asset_id, []), day)
        if close is None:
            return None
        fx = self._fx_rate(f"{self._currency[asset_id]}EUR", day)
        return None if fx is None else close * fx

    def _fx_rate(self, pair: str, day: date) -> Decimal | None:
        key = (pair, day)
        if key not in self._fx:
            try:
                quote = prices.fx_quote(pair, end_of(day))
            except AppError:
                self._fx[key] = None
            else:
                self._fx[key] = quote.rate
                if pair[:3] != pair[3:]:
                    self.sources[(quote.source.kind, quote.source.ref)] = quote.source
        return self._fx[key]


# --- Serie de la cartera ---


def _load_transactions(portfolio_id: str, until: datetime) -> list[TxIn]:
    with session_scope() as session:
        if repository.get_portfolio(session, portfolio_id) is None:
            raise errors.portfolio_not_found(portfolio_id)
        return ledger.transactions_until(session, portfolio_id, until)


def _no_prices(portfolio_id: str, period: HistoryPeriod) -> AppError:
    return AppError(
        ErrorCode.PRICE_UNAVAILABLE,
        "No hay precios para valorar la cartera en ese periodo.",
        details={"portfolio_id": portfolio_id, "period": period.value},
    )


def get_history(portfolio_id: str, period: HistoryPeriod) -> PortfolioHistoryOut:
    """Valor de la cartera en cada día del periodo. Deja traza `valuation`."""
    today = clock.now().date()
    txs = _load_transactions(portfolio_id, end_of(today))
    if not txs:
        raise _no_prices(portfolio_id, period)
    first_day = min(tx.ts for tx in txs).date()
    quotes = _Prices({tx.asset_id for tx in txs}, first_day, today)
    sampled = sample_days(quotes.last_market_day(today), period, first_day)
    days = [d for d in sampled if quotes.is_market_day(d)]
    points: list[PortfolioHistoryPoint] = []
    for day in days:
        units = value_change.units_at(txs, end_of(day))
        value = day_value(units, {a: quotes.unit_eur(a, day) for a in units})
        if value is not None:
            midnight = datetime.combine(day, time(0), tzinfo=UTC)
            points.append(PortfolioHistoryPoint(date=midnight, value_eur=value))
    if not points:
        raise _no_prices(portfolio_id, period)
    first, last = points[0].date.date(), points[-1].date.date()
    flows = value_change.flows_between(txs, end_of(first), end_of(last))
    net_flows = sum(flows.values(), Decimal(0)).quantize(CENT, rounding=ROUND_HALF_EVEN)
    sources = list(quotes.sources.values())
    calc_id = trace.record(
        TraceKind.VALUATION,
        FORMULA,
        inputs={
            "portfolio_id": portfolio_id,
            "period": period.value,
            "days": [d.isoformat() for d in days],
            "transactions": [
                {"asset_id": t.asset_id, "ts": t.ts, "type": t.type, "units": t.units} for t in txs
            ],
        },
        outputs={
            "points": [[p.date.date().isoformat(), p.value_eur] for p in points],
            "start_value_eur": points[0].value_eur,
            "end_value_eur": points[-1].value_eur,
            "net_flows_eur": net_flows,
        },
        sources=sources,
    )
    return PortfolioHistoryOut(
        portfolio_id=portfolio_id,
        period=period,
        points=points,
        start_value_eur=points[0].value_eur,
        end_value_eur=points[-1].value_eur,
        net_flows_eur=net_flows,
        calc_id=calc_id,
        sources=sources,
    )
