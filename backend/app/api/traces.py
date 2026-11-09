"""Trazabilidad de cifras (diseño del MVP §4.1, RF-19): de dónde sale cualquier número.

Cada cifra que muestra la app lleva un `calc_id`. Esta ruta devuelve su traza (fórmula, entradas,
resultado, fuentes y fecha) y, en `parent_calc_ids`, las trazas de las que deriva, para que el
frontend pueda seguir la cadena llamando de nuevo con cada una.
"""

from typing import Any

from fastapi import APIRouter

from app.core import trace
from app.core.errors import AppError, ErrorCode
from app.schemas.common import ErrorOut, SourceRef, TraceKind
from app.schemas.portfolio import TraceOut

router = APIRouter(tags=["traces"])

_NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"model": ErrorOut}}


@router.get("/traces/{calc_id}", response_model=TraceOut, responses=_NOT_FOUND)
def get_trace(calc_id: str) -> TraceOut:
    record = trace.get(calc_id)
    if record is None:
        raise AppError(
            ErrorCode.NOT_FOUND, "No existe el cálculo que has pedido.", {"calc_id": calc_id}
        )
    return TraceOut(
        calc_id=record.calc_id,
        kind=TraceKind(record.kind),
        created_at=record.created_at,
        formula=record.formula,
        inputs=record.inputs,
        outputs=record.outputs,
        sources=[SourceRef.model_validate(source) for source in record.sources],
        parent_calc_ids=record.parent_calc_ids,
    )
