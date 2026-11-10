"""Caché de precios en BD (tablas `price` y `fx_rate`, `SPEC.md` §6). Solo la usa el proveedor en
directo (T2-24): el offline lee los CSV y no guarda nada.

Cada fila es `(ts, valor)`: los cierres diarios van a las 00:00 UTC de su sesión y el último
precio en el instante que da el proveedor. Guardar es idempotente: una fila con el mismo `ts` se
actualiza, no se duplica.
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select

from app.core.db import session_scope
from app.prices.models import FxRate, Price

Row = tuple[datetime, Decimal]


def _utc(value: datetime) -> datetime:
    """SQLite devuelve las fechas sin zona; en BD siempre son UTC."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def load_prices(asset_id: str) -> list[Row]:
    with session_scope() as session:
        rows = session.execute(
            select(Price.ts, Price.value).where(Price.asset_id == asset_id).order_by(Price.ts)
        ).all()
    return [(_utc(ts), value) for ts, value in rows]


def save_prices(asset_id: str, currency: str, rows: Sequence[Row], source: str) -> None:
    if not rows:
        return
    with session_scope() as session:
        existing = {
            _utc(item.ts): item
            for item in session.scalars(select(Price).where(Price.asset_id == asset_id))
        }
        for ts, value in rows:
            item = existing.get(_utc(ts))
            if item is None:
                session.add(
                    Price(asset_id=asset_id, ts=ts, value=value, currency=currency, source=source)
                )
            elif item.value != value:
                item.value, item.source = value, source


def load_fx(pair: str) -> list[Row]:
    with session_scope() as session:
        rows = session.execute(
            select(FxRate.ts, FxRate.rate).where(FxRate.pair == pair).order_by(FxRate.ts)
        ).all()
    return [(_utc(ts), rate) for ts, rate in rows]


def save_fx(pair: str, rows: Sequence[Row], source: str) -> None:
    if not rows:
        return
    with session_scope() as session:
        existing = {
            _utc(item.ts): item
            for item in session.scalars(select(FxRate).where(FxRate.pair == pair))
        }
        for ts, rate in rows:
            item = existing.get(_utc(ts))
            if item is None:
                session.add(FxRate(pair=pair, ts=ts, rate=rate, source=source))
            elif item.rate != rate:
                item.rate, item.source = rate, source
