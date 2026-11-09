"""Trazabilidad de cifras (`calc_trace`). Toda cifra mostrada lleva un `calc_id` que apunta aquí.

Interfaz pública (diseño del MVP §4.1):

    record(kind, formula, inputs, outputs, sources, parent_calc_ids=[]) -> calc_id
    get(calc_id) -> TraceRecord | None

`GET /traces/{calc_id}` (`app/api/traces.py`) sirve una traza tal cual; las cifras derivadas de
varias trazas apuntan a las de origen con `parent_calc_ids`.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel
from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core import clock
from app.core.db import Base, session_scope
from app.schemas.common import SourceRef, TraceKind


class CalcTrace(Base):
    __tablename__ = "calc_trace"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), index=True)
    formula: Mapped[str] = mapped_column(Text, default="")
    inputs: Mapped[dict[str, Any]] = mapped_column(JSON)
    outputs: Mapped[dict[str, Any]] = mapped_column(JSON)
    sources: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    parent_calc_ids: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


@dataclass(frozen=True)
class TraceRecord:
    calc_id: str
    kind: str
    formula: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    sources: list[dict[str, Any]]
    parent_calc_ids: list[str]
    created_at: datetime


def new_calc_id() -> str:
    return "calc_" + uuid.uuid4().hex


def to_jsonable(value: Any) -> Any:
    """Convierte Decimal, fechas, enums y modelos Pydantic a JSON. Los Decimal van como string."""
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime | date):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, list | tuple | set):
        return [to_jsonable(v) for v in value]
    return value


def record(
    kind: TraceKind | str,
    formula: str,
    inputs: dict[str, Any],
    outputs: dict[str, Any],
    sources: list[SourceRef],
    parent_calc_ids: list[str] | None = None,
) -> str:
    """Guarda una traza y devuelve su `calc_id`."""
    kind_value = TraceKind(kind).value
    calc_id = new_calc_id()
    row = CalcTrace(
        id=calc_id,
        kind=kind_value,
        formula=formula,
        inputs=to_jsonable(inputs),
        outputs=to_jsonable(outputs),
        sources=[s.model_dump(mode="json") for s in sources],
        parent_calc_ids=list(parent_calc_ids or []),
        created_at=clock.now(),
    )
    with session_scope() as session:
        session.add(row)
    return calc_id


def _with_zone(value: datetime) -> datetime:
    """Fecha con zona. Postgres (`timestamptz`) ya la devuelve con zona: no se toca. SQLite la
    devuelve sin zona: se asume UTC, que es como se guarda (`clock.now()` es siempre UTC)."""
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def get(calc_id: str) -> TraceRecord | None:
    with session_scope() as session:
        row = session.get(CalcTrace, calc_id)
        if row is None:
            return None
        return TraceRecord(
            calc_id=row.id,
            kind=row.kind,
            formula=row.formula,
            inputs=row.inputs,
            outputs=row.outputs,
            sources=row.sources,
            parent_calc_ids=row.parent_calc_ids,
            created_at=_with_zone(row.created_at),
        )
