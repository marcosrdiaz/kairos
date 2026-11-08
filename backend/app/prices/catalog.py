"""Qué necesita `prices` de cada activo: divisa, tipo de precio y fuente.

Sale de `data/seed/assets.json` (D-038), el mismo catálogo que carga `seed_db.py` en la tabla
`asset`. `prices` no consulta esa tabla, que es de `portfolio` (y `portfolio` depende de `prices`).
"""

import json
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from app.schemas.common import PriceKind

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


def _parse(raw: dict[str, object]) -> AssetPriceSpec:
    source = str(raw["price_source"])
    kind, _, value = source.partition(":")
    if kind not in {"yahoo", "fixed"} or not value:
        raise ValueError(f"price_source no válido en {raw['id']}: {source!r}")
    return AssetPriceSpec(
        asset_id=str(raw["id"]),
        name=str(raw["name"]),
        currency=str(raw["currency"]),
        price_kind=PriceKind(str(raw["price_kind"])),
        symbol=value if kind == "yahoo" else None,
        fixed_price=Decimal(value) if kind == "fixed" else None,
    )


@lru_cache
def load_catalog(path: Path = DEFAULT_ASSETS_FILE) -> dict[str, AssetPriceSpec]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {spec.asset_id: spec for spec in map(_parse, data["assets"])}
