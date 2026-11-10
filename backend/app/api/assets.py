"""Catálogo de activos: autocompletar del alta (RF-01) y alta de activos nuevos (T4-07)."""

import logging
from typing import Any

from fastapi import APIRouter, Query, status

from app.impact import service as impact_service
from app.portfolio import service
from app.schemas.common import ErrorOut
from app.schemas.portfolio import AssetCreateRequest, AssetOut

log = logging.getLogger(__name__)
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
    """
    asset, created = service.register_asset(body.query)
    if created:
        try:  # sin datos suficientes, el activo queda «sin betas» (D-050); el alta sigue valiendo
            impact_service.recompute_betas([asset.id])
        except Exception:
            log.exception("Betas del activo nuevo %s: no se han podido calcular", asset.id)
    return asset
