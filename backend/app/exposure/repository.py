"""Acceso a la tabla `composition`. Solo aquí se consulta."""

from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import delete, select

from app.core.db import session_scope
from app.exposure.models import Composition


@dataclass(frozen=True)
class CompositionRow:
    fund_asset_id: str
    constituent_key: str
    name: str
    weight: Decimal
    country: str | None
    sector: str | None
    currency: str | None
    as_of: date
    source: str


def _row(r: Composition) -> CompositionRow:
    return CompositionRow(
        fund_asset_id=r.fund_asset_id,
        constituent_key=r.constituent_key,
        name=r.name,
        weight=r.weight,
        country=r.country,
        sector=r.sector,
        currency=r.currency,
        as_of=r.as_of,
        source=r.source,
    )


def replace_compositions(rows: Sequence[CompositionRow]) -> int:
    """Sustituye la composición de los fondos recibidos. Idempotente."""
    funds = {row.fund_asset_id for row in rows}
    with session_scope() as session:
        session.execute(delete(Composition).where(Composition.fund_asset_id.in_(funds)))
        session.add_all(
            Composition(
                fund_asset_id=row.fund_asset_id,
                constituent_key=row.constituent_key,
                name=row.name,
                weight=row.weight,
                country=row.country,
                sector=row.sector,
                currency=row.currency,
                as_of=row.as_of,
                source=row.source,
            )
            for row in rows
        )
    return len(rows)


def get_compositions(asset_ids: Iterable[str]) -> list[CompositionRow]:
    with session_scope() as session:
        rows = session.scalars(
            select(Composition)
            .where(Composition.fund_asset_id.in_(list(asset_ids)))
            .order_by(Composition.fund_asset_id, Composition.constituent_key)
        ).all()
        return [_row(r) for r in rows]


def get_named_rows(asset_ids: Iterable[str], companies: Collection[str]) -> list[CompositionRow]:
    """Filas de esas empresas dentro de esos fondos."""
    with session_scope() as session:
        rows = session.scalars(
            select(Composition).where(
                Composition.fund_asset_id.in_(list(asset_ids)),
                Composition.constituent_key.in_(list(companies)),
            )
        ).all()
        return [_row(r) for r in rows]


def latest_by_key(keys: Collection[str]) -> dict[str, CompositionRow]:
    """Para cada empresa, su fila más reciente en cualquier fondo (iShares va por delante)."""
    with session_scope() as session:
        rows = session.scalars(
            select(Composition)
            .where(Composition.constituent_key.in_(list(keys)))
            .order_by(Composition.as_of, Composition.fund_asset_id)
        ).all()
        return {r.constituent_key: _row(r) for r in rows}
