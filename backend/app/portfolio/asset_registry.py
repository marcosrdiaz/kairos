"""Catálogo abierto (T4-07): dar de alta un activo que no está en `assets.json`.

- `register_asset(query)`: si ya está en la tabla `asset` (id, ISIN, ticker o símbolo exactos),
  lo devuelve. Si no, lo busca en el proveedor en directo (`prices.service.discover_asset`) y lo
  guarda en `asset` con divisa, clase, `price_kind` y `price_source`. Su histórico lo pide y lo
  guarda `prices` la primera vez que se valora (3 años, T2-24); las betas, quien lo da de alta
  (`api/assets.py`, con `impact.service.recompute_betas`).
- `install()`: le da a `prices` una extensión del catálogo con los activos de `asset`, para que
  sepa valorarlos sin consultar esta tabla, que es de `portfolio`.

Id del activo nuevo: el ISIN si la consulta lo era (Yahoo no lo devuelve); si no, `YF-<símbolo>`.
Un fondo se marca traspasable (fondo de inversión); el TER no se conoce y queda `null`.
"""

from decimal import ROUND_HALF_EVEN, Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.db import session_scope
from app.core.errors import AppError, ErrorCode
from app.portfolio import repository
from app.portfolio.models import Asset
from app.prices import service as prices_service
from app.prices.service import AssetPriceSpec
from app.schemas.common import AssetClass, AssetType, PriceKind
from app.schemas.portfolio import AssetOut

_TER_STEP = Decimal("0.0001")


def _out(row: Asset) -> AssetOut:
    return AssetOut(
        id=row.id,
        isin=row.isin,
        ticker=row.ticker,
        name=row.name,
        asset_type=AssetType(row.asset_type),
        asset_class=AssetClass(row.asset_class),
        currency=row.currency,
        ter=None if row.ter is None else row.ter.quantize(_TER_STEP, ROUND_HALF_EVEN),
        transferable=row.transferable,
        price_kind=PriceKind(row.price_kind),
    )


def _exact(session: Session, query: str) -> Asset | None:
    wanted = query.strip().lower()
    return session.scalars(
        select(Asset)
        .where(
            or_(
                func.lower(Asset.id) == wanted,
                func.lower(func.coalesce(Asset.isin, "")) == wanted,
                func.lower(func.coalesce(Asset.ticker, "")) == wanted,
                func.lower(Asset.price_source) == f"yahoo:{wanted}",
            )
        )
        .order_by(Asset.id)
        .limit(1)
    ).first()


def register_asset(query: str) -> tuple[AssetOut, bool]:
    """El activo y si se ha creado ahora. 404 si el proveedor no lo conoce; 503 si no responde
    o si no hay precios en directo."""
    text = query.strip()
    with session_scope() as session:
        known = _exact(session, text)
        if known is not None:
            return _out(known), False

    found = prices_service.discover_asset(text)
    if found is None:
        raise AppError(
            ErrorCode.NOT_FOUND,
            f"No encontramos «{text}» en el proveedor de precios. Prueba con el ISIN o con el "
            "ticker exacto (p. ej. VWCE.DE).",
            details={"query": text},
        )

    with session_scope() as session:
        same = session.scalars(
            select(Asset).where(Asset.price_source == found.price_source).limit(1)
        ).first()
        if same is not None:
            return _out(same), False
        asset_id = found.isin or f"YF-{found.symbol.upper()}"
        existing = session.get(Asset, asset_id)
        if existing is not None:
            return _out(existing), False
        repository.upsert_assets(
            session,
            [
                {
                    "id": asset_id,
                    "isin": found.isin,
                    "ticker": found.symbol.split(".")[0].upper(),
                    "name": found.name,
                    "asset_type": found.asset_type.value,
                    "asset_class": found.asset_class.value,
                    "currency": found.currency,
                    "ter": None,
                    "transferable": found.asset_type is AssetType.FUND,
                    "price_kind": found.price_kind.value,
                    "price_source": found.price_source,
                }
            ],
        )
        row = session.get(Asset, asset_id)
        assert row is not None
        return _out(row), True


# --- Extensión del catálogo de `prices` ---


def _spec(asset_id: str) -> AssetPriceSpec | None:
    with session_scope() as session:
        row = session.get(Asset, asset_id)
        if row is None:
            return None
        return prices_service.parse_spec(
            row.id, row.name, row.currency, row.price_kind, row.price_source
        )


def _ids() -> list[str]:
    with session_scope() as session:
        return list(session.scalars(select(Asset.id).order_by(Asset.id)))


def install() -> None:
    prices_service.set_catalog_extension(_spec, _ids)
