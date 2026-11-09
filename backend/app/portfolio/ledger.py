"""Acceso al libro de operaciones (`transaction`) y a los lotes (`tax_lot`). Lo usan
`service.py`, `operations.py` y `seed.py`.

Todas las funciones reciben la sesión: la transacción la abre y la cierra quien llama.
"""

from collections.abc import Iterable
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.portfolio.engine import LotIn
from app.portfolio.lots import OpenLot
from app.portfolio.models import TaxLot, Transaction
from app.portfolio.repository import new_id, utc

_CENT = Decimal("0.01")


def add_transaction(session: Session, portfolio_id: str, **values: Any) -> str:
    """Apunta una operación en el libro (columnas de `Transaction`). Devuelve su id (`tx_…`)."""
    tx_id = new_id("tx")
    session.add(Transaction(id=tx_id, portfolio_id=portfolio_id, **values))
    session.flush()
    return tx_id


def add_lot(
    session: Session, portfolio_id: str, asset_id: str, lot: OpenLot, origin_tx_id: str
) -> str:
    """Abre un lote con las participaciones, fecha y coste de `lot`. Devuelve su id (`lot_…`)."""
    lot_id = new_id("lot")
    session.add(
        TaxLot(
            id=lot_id,
            portfolio_id=portfolio_id,
            asset_id=asset_id,
            acquired_at=lot.acquired_at,
            units_initial=lot.units,
            units_remaining=lot.units,
            cost_eur_per_unit=lot.cost_eur_per_unit,
            origin_tx_id=origin_tx_id,
        )
    )
    return lot_id


def add_initial_lot(
    session: Session,
    portfolio_id: str,
    asset_id: str,
    acquired_at: datetime,
    units: Decimal,
    cost_eur_per_unit: Decimal,
) -> str:
    """Alta (`initial`): una operación en el libro y su lote. Devuelve el id de la operación."""
    tx_id = add_transaction(
        session,
        portfolio_id,
        type="initial",
        asset_id=asset_id,
        units=units,
        ts=acquired_at,
        price=cost_eur_per_unit,
        price_currency="EUR",
        fx_rate=Decimal(1),
        amount_eur=(units * cost_eur_per_unit).quantize(_CENT, rounding=ROUND_HALF_EVEN),
    )
    lot = OpenLot("", acquired_at, units, cost_eur_per_unit)
    add_lot(session, portfolio_id, asset_id, lot, tx_id)
    return tx_id


def asset_lots(session: Session, portfolio_id: str, asset_id: str) -> list[OpenLot]:
    """Lotes abiertos de un activo en orden FIFO (por fecha de adquisición)."""
    stmt = (
        select(TaxLot)
        .where(
            TaxLot.portfolio_id == portfolio_id,
            TaxLot.asset_id == asset_id,
            TaxLot.units_remaining > 0,
        )
        .order_by(TaxLot.acquired_at, TaxLot.id)
    )
    return [
        OpenLot(
            lot_id=row.id,
            acquired_at=utc(row.acquired_at),
            units=row.units_remaining,
            cost_eur_per_unit=row.cost_eur_per_unit,
        )
        for row in session.scalars(stmt)
    ]


def consume_lots(session: Session, consumed: Iterable[OpenLot]) -> None:
    """Resta de cada lote las participaciones vendidas (`OpenLot.units` = lo consumido)."""
    for part in consumed:
        session.execute(
            update(TaxLot)
            .where(TaxLot.id == part.lot_id)
            .values(units_remaining=TaxLot.units_remaining - part.units)
        )


def open_lots(session: Session, portfolio_id: str) -> list[LotIn]:
    stmt = (
        select(TaxLot)
        .where(TaxLot.portfolio_id == portfolio_id, TaxLot.units_remaining > 0)
        .order_by(TaxLot.asset_id, TaxLot.acquired_at, TaxLot.id)
    )
    return [
        LotIn(
            asset_id=row.asset_id,
            acquired_at=utc(row.acquired_at),
            units=row.units_remaining,
            cost_eur_per_unit=row.cost_eur_per_unit,
        )
        for row in session.scalars(stmt)
    ]
