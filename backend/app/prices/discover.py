"""Buscar en el proveedor en directo un activo que no está en el catálogo (T4-07).

1. Búsqueda de Yahoo por ISIN, ticker o nombre; solo acciones, ETF y fondos.
2. De los primeros resultados, el primero con precios y en una divisa que sabemos convertir
   (EUR o USD: el único tipo de cambio en directo es EUR/USD). Una cotización en peniques
   (`GBp`) u otra divisa se salta: valorarla daría una cifra errónea.
3. Clase de activo: acciones, renta variable; ETF y fondos, renta fija si el nombre lo dice
   («bond», «treasury», «aggregate»…), si no, renta variable. Es una aproximación a partir del
   nombre (no hay otra fuente sin clave) y queda documentada en la decisión de T4-07.

Sin dependencias nuevas: el mismo `YahooClient` de T2-24.
"""

import re
from dataclasses import dataclass
from typing import Protocol

from app.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.prices.yahoo import Chart, ProviderError, Quote, YahooClient
from app.schemas.common import AssetClass, AssetType, PriceKind

ISIN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
SUPPORTED_TYPES = {
    "EQUITY": AssetType.STOCK,
    "ETF": AssetType.ETF,
    "MUTUALFUND": AssetType.FUND,
}
SUPPORTED_CURRENCIES = frozenset({"EUR", "USD"})
MAX_CANDIDATES = 5
_FIXED_INCOME_WORDS = (
    "bond",
    "govt",
    "government",
    "treasury",
    "aggregate",
    "corporate",
    "credit",
    "fixed income",
    "inflation",
    "money market",
    "renta fija",
    "monetario",
)


class SearchSource(Protocol):
    def search(self, query: str) -> list[Quote]: ...

    def chart(self, symbol: str, range_: str) -> Chart: ...


@dataclass(frozen=True)
class DiscoveredAsset:
    symbol: str
    name: str
    currency: str
    asset_type: AssetType
    asset_class: AssetClass
    price_kind: PriceKind
    isin: str | None
    """La consulta, si era un ISIN (Yahoo no lo devuelve)."""

    @property
    def price_source(self) -> str:
        return f"yahoo:{self.symbol}"


def normalize_isin(query: str) -> str | None:
    candidate = query.strip().upper()
    return candidate if ISIN.match(candidate) else None


def asset_class_for(asset_type: AssetType, name: str) -> AssetClass:
    if asset_type is AssetType.STOCK:
        return AssetClass.EQUITY
    lowered = name.lower()
    if any(word in lowered for word in _FIXED_INCOME_WORDS):
        return AssetClass.FIXED_INCOME
    return AssetClass.EQUITY


def _usable(chart: Chart) -> bool:
    has_prices = bool(chart.closes) or chart.last_price is not None
    return has_prices and chart.currency in SUPPORTED_CURRENCIES


def discover(query: str, source: SearchSource) -> DiscoveredAsset | None:
    """El primer resultado utilizable de la búsqueda, o `None` si el proveedor no conoce nada.

    Lanza `ProviderError` si la búsqueda falla o si ningún candidato ha podido comprobarse
    porque el proveedor no respondía.
    """
    quotes = [q for q in source.search(query.strip()) if q.quote_type in SUPPORTED_TYPES]
    errors: list[str] = []
    for quote in quotes[:MAX_CANDIDATES]:
        try:
            chart = source.chart(quote.symbol, "5d")
        except ProviderError as error:
            errors.append(str(error))
            continue
        if not _usable(chart):
            continue
        asset_type = SUPPORTED_TYPES[quote.quote_type]
        return DiscoveredAsset(
            symbol=quote.symbol,
            name=quote.name,
            currency=str(chart.currency),
            asset_type=asset_type,
            asset_class=asset_class_for(asset_type, quote.name),
            price_kind=PriceKind.NAV_DAILY if asset_type is AssetType.FUND else PriceKind.INTRADAY,
            isin=normalize_isin(query),
        )
    if errors and len(errors) == len(quotes[:MAX_CANDIDATES]):
        raise ProviderError("; ".join(errors))
    return None


_search: SearchSource | None = None


def set_search_source(source: SearchSource | None) -> SearchSource | None:
    """Cambia la búsqueda del catálogo abierto (tests). Devuelve la anterior."""
    global _search
    previous, _search = _search, source
    return previous


def discover_asset(query: str) -> DiscoveredAsset | None:
    """`discover` con el proveedor en directo (`prices.service.discover_asset`). `None` si no
    conoce el activo. Solo con precios en directo: en modo demo no habría con qué valorarlo."""
    if _search is None and get_settings().market_data_provider != "yahoo":
        raise AppError(
            ErrorCode.UPSTREAM_UNAVAILABLE,
            "Dar de alta activos nuevos necesita precios en directo; en modo demo solo están "
            "los del catálogo.",
            details={"query": query},
        )
    try:
        return discover(query, _search or YahooClient())
    except ProviderError as error:
        raise AppError(
            ErrorCode.UPSTREAM_UNAVAILABLE,
            "El proveedor de precios no responde; prueba de nuevo en unos minutos.",
            details={"query": query, "reason": str(error)},
        ) from error
