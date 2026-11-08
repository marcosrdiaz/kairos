"""Catálogo de activos: autocompletar del alta (RF-01)."""

from fastapi import APIRouter, Query

from app.portfolio import service
from app.schemas.portfolio import AssetOut

router = APIRouter(tags=["assets"])


@router.get("/assets/lookup", response_model=list[AssetOut])
def lookup_assets(q: str = Query(min_length=1, max_length=80)) -> list[AssetOut]:
    """Busca por ISIN, ticker o nombre. Lista vacía si no hay coincidencias."""
    return service.lookup_assets(q)
