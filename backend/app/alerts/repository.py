"""Acceso a la tabla `alert`. Solo aquí se abren sesiones."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select

from app.alerts.models import Alert
from app.core.db import session_scope
from app.schemas.alerts import AlertKind


@dataclass(frozen=True)
class StoredAlert:
    id: str
    event_id: str | None
    kind: AlertKind
    score: Decimal
    message: str
    created_at: datetime
    delivered: bool


def _utc(value: datetime) -> datetime:
    """SQLite devuelve las fechas sin zona; se guardan siempre en UTC."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _stored(row: Alert) -> StoredAlert:
    return StoredAlert(
        id=row.id,
        event_id=row.event_id,
        kind=AlertKind(row.kind),
        score=row.score,
        message=row.message,
        created_at=_utc(row.created_at),
        delivered=row.delivered,
    )


def exists(portfolio_id: str, event_id: str, kind: AlertKind) -> bool:
    with session_scope() as session:
        found = session.scalar(
            select(Alert.id)
            .where(
                Alert.portfolio_id == portfolio_id,
                Alert.event_id == event_id,
                Alert.kind == kind.value,
            )
            .limit(1)
        )
        return found is not None


def count_between(portfolio_id: str, start: datetime, end: datetime) -> int:
    """Avisos de la cartera creados en [`start`, `end`), sin contar los `dca_pending`."""
    with session_scope() as session:
        return (
            session.scalar(
                select(func.count())
                .select_from(Alert)
                .where(
                    Alert.portfolio_id == portfolio_id,
                    Alert.kind != AlertKind.DCA_PENDING.value,
                    Alert.created_at >= start.astimezone(UTC),
                    Alert.created_at < end.astimezone(UTC),
                )
            )
            or 0
        )


def save(
    portfolio_id: str,
    event_id: str | None,
    kind: AlertKind,
    score: Decimal,
    message: str,
    created_at: datetime,
) -> StoredAlert:
    row = Alert(
        id=f"alr_{uuid.uuid4().hex}",
        portfolio_id=portfolio_id,
        event_id=event_id,
        kind=kind.value,
        score=score,
        message=message,
        created_at=created_at.astimezone(UTC),
        delivered=False,
    )
    with session_scope() as session:
        session.add(row)
        session.flush()
        return _stored(row)


def list_for(portfolio_id: str) -> list[StoredAlert]:
    """Del más reciente al más antiguo."""
    with session_scope() as session:
        rows = session.scalars(
            select(Alert)
            .where(Alert.portfolio_id == portfolio_id)
            .order_by(Alert.created_at.desc(), Alert.id)
        ).all()
        return [_stored(r) for r in rows]
