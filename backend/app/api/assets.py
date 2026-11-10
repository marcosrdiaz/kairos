"""Catálogo de activos: autocompletar del alta (RF-01) y alta de activos nuevos (T4-07)."""

from typing import Any

from fastapi import APIRouter, Query, status

from app.portfolio import service
from app.schemas import examples
from app.schemas.common import ErrorOut
from app.schemas.portfolio import AssetCreateRequest, AssetOut

router = APIRouter(tags=["assets"])

_ERRORS: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorOut},
    422: {"model": ErrorOut},
    503: {"model": ErrorOut},
}


@router.get("/assets/lookup", response_model=list[AssetOut])
def lookup_assets(q: str = Query(min_length=1, max_length=80)) -> list[AssetOut]:
    """Busca por ISIN, ticker o nombre. Lista vacía si no hay coincidencias."""
    return service.lookup_assets(q)


@router.post(
    "/assets",
    response_model=AssetOut,
    status_code=status.HTTP_201_CREATED,
    responses=_ERRORS,
)
def create_asset(body: AssetCreateRequest) -> AssetOut:
    """Da de alta un activo que no está en el catálogo buscándolo en el proveedor en directo
    (ISIN, ticker o nombre), con su histórico y sus betas. Si ya está, devuelve el del catálogo.
    404 `NOT_FOUND` si el proveedor no lo conoce; 503 `UPSTREAM_UNAVAILABLE` si no responde o si
    no hay precios en directo (modo demo).

    Contrato (T4-07): sirve el ejemplo hasta la implementación.
    """
    return AssetOut.model_validate(examples.load("AssetOut"))
