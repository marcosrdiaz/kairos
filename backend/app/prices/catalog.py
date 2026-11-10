"""Qué necesita `prices` de cada activo: divisa, tipo de precio y fuente.

Dos orígenes (T4-07, catálogo abierto):

- `data/seed/assets.json` (D-038), el catálogo base que carga `seed_db.py` en la tabla `asset`.
- Los activos dados de alta después (`POST /assets`). Viven en la tabla `asset`, que es de
  `portfolio`; `prices` no la consulta: `portfolio` le da una extensión (`set_extension`) con una
  función que devuelve la ficha de un activo y otra que lista los dados de alta.

El catálogo base manda: un activo de `assets.json` nunca se busca en la extensión.
"""

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from app.schemas.common import PriceKind

log = logging.getLogger(__name__)

DEFAULT_ASSETS_FILE = Path(__file__).resolve().parents[3] / "data" / "seed" / "assets.json"


@dataclass(frozen=True)
class AssetPriceSpec:
    asset_id: str
    name: str
    currency: str
    price_kind: PriceKind
    symbol: str | None
    """Símbolo de `yahoo:<símbolo>`; `None` si el precio es fijo."""
    fixed_price: Decimal | None
    """Valor de `fixed:<valor>` (depósito, plan de pensiones): sin histórico ni betas."""


def parse_spec(
    asset_id: str, name: str, currency: str, price_kind: str, price_source: str
) -> AssetPriceSpec:
    """Ficha de precio a partir de las columnas de `asset` (o de una fila de `assets.json`)."""
    kind, _, value = price_source.partition(":")
    if kind not in {"yahoo", "fixed"} or not value:
        raise ValueError(f"price_source no válido en {asset_id}: {price_source!r}")
    return AssetPriceSpec(
        asset_id=asset_id,
        name=name,
        currency=currency,
        price_kind=PriceKind(price_kind),
        symbol=value if kind == "yahoo" else None,
        fixed_price=Decimal(value) if kind == "fixed" else None,
    )


def _parse(raw: dict[str, object]) -> AssetPriceSpec:
    return parse_spec(
        str(raw["id"]),
        str(raw["name"]),
        str(raw["currency"]),
        str(raw["price_kind"]),
        str(raw["price_source"]),
    )


@lru_cache
def load_catalog(path: Path = DEFAULT_ASSETS_FILE) -> dict[str, AssetPriceSpec]:
    """Catálogo base (`assets.json`). Para buscar un activo cualquiera, `get_spec`."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return {spec.asset_id: spec for spec in map(_parse, data["assets"])}


SpecLookup = Callable[[str], AssetPriceSpec | None]
IdsLookup = Callable[[], list[str]]

_extension: tuple[SpecLookup, IdsLookup] | None = None


def set_extension(get: SpecLookup | None, ids: IdsLookup | None = None) -> None:
    """La pone `portfolio` al importarse: activos dados de alta fuera de `assets.json`."""
    global _extension
    _extension = None if get is None else (get, ids or (lambda: []))


def get_spec(asset_id: str) -> AssetPriceSpec | None:
    spec = load_catalog().get(asset_id)
    if spec is not None or _extension is None:
        return spec
    try:
        return _extension[0](asset_id)
    except Exception:  # sin BD (scripts, tests puros): solo el catálogo base
        log.debug("Extensión del catálogo no disponible para %s", asset_id, exc_info=True)
        return None


def all_asset_ids() -> list[str]:
    """Catálogo base y, después, los dados de alta."""
    base = list(load_catalog())
    if _extension is None:
        return base
    try:
        extra = _extension[1]()
    except Exception:
        log.debug("Extensión del catálogo no disponible", exc_info=True)
        extra = []
    known = set(base)
    return base + [a for a in extra if a not in known]
