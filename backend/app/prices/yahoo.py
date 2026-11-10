"""Cliente HTTP de Yahoo Finance para los precios en directo (T2-24, D-065).

Usa el mismo endpoint que `scripts/fetch_prices.py` (D-045): `v8/finance/chart/<símbolo>`, sin
clave. Una llamada devuelve los cierres diarios del periodo pedido y, en `meta`, el último precio
con su instante y la sesión regular del día. Los números se leen como `Decimal` (nunca `float`).

Yahoo no tiene API oficial ni acuerdo de servicio: vale para el piloto, no para un lanzamiento
(D-065). Otro proveedor con licencia sería otra clase con el mismo método `chart`.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from app.core import clock

CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"
TIMEOUT_S = 5.0
_STEP = Decimal("0.00000001")  # NUMERIC(20,8)


class ProviderError(Exception):
    """El proveedor no respondió o respondió algo que no se puede usar."""


@dataclass(frozen=True)
class Chart:
    closes: list[tuple[date, Decimal]]
    """Cierre (o VL) de cada sesión, en orden de fecha. La de hoy puede estar aún abierta."""
    last_price: Decimal | None
    last_at: datetime | None
    """Instante del último precio según el proveedor (no el de la petición)."""
    market_open: bool
    """Si la sesión regular está abierta en el momento de la petición."""
    next_open: datetime | None
    """Apertura de la sesión de hoy si aún no ha empezado; `None` si no se sabe o ya pasó."""
    currency: str | None = None
    """Divisa de cotización según el proveedor (T4-07); `None` si no la da."""


@dataclass(frozen=True)
class Quote:
    """Un resultado de la búsqueda de Yahoo (T4-07)."""

    symbol: str
    name: str
    quote_type: str
    """`EQUITY`, `ETF`, `MUTUALFUND`…"""


def _decimal(value: object) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        return None
    if not number.is_finite() or number <= 0:
        return None
    return number.quantize(_STEP)


def _instant(value: object) -> datetime | None:
    if not isinstance(value, int | Decimal) or isinstance(value, bool):
        return None
    return datetime.fromtimestamp(int(value), UTC)


def _bar_date(instant: datetime) -> date:
    """Fecha de sesión de una barra diaria: según el mercado empieza a medianoche local o en la
    apertura; sumar 6 h deja el mismo día natural en las zonas del catálogo (como en
    `fetch_prices.py`)."""
    return (instant + timedelta(hours=6)).date()


def parse_chart(payload: dict[str, Any], now: datetime) -> Chart:
    try:
        result = payload["chart"]["result"][0]
        meta: dict[str, Any] = result["meta"]
        stamps: list[object] = result.get("timestamp") or []
        closes_raw: list[object] = result["indicators"]["quote"][0].get("close") or []
    except (KeyError, IndexError, TypeError) as error:
        raise ProviderError("respuesta de Yahoo sin datos") from error

    closes: dict[date, Decimal] = {}
    for stamp, raw in zip(stamps, closes_raw, strict=False):
        instant, value = _instant(stamp), _decimal(raw)
        if instant is not None and value is not None:
            closes[_bar_date(instant)] = value

    last_price = _decimal(meta.get("regularMarketPrice"))
    last_at = _instant(meta.get("regularMarketTime"))
    if last_price is None or last_at is None:
        last_price, last_at = None, None
    if not closes and last_price is None:
        raise ProviderError("respuesta de Yahoo sin precios")

    regular = (meta.get("currentTradingPeriod") or {}).get("regular") or {}
    start, end = _instant(regular.get("start")), _instant(regular.get("end"))
    market_open = start is not None and end is not None and start <= now < end
    next_open = start if start is not None and now < start else None
    currency = meta.get("currency")
    return Chart(
        closes=sorted(closes.items()),
        last_price=last_price,
        last_at=last_at,
        market_open=market_open,
        next_open=next_open,
        currency=currency if isinstance(currency, str) and currency else None,
    )


def parse_search(payload: dict[str, Any]) -> list[Quote]:
    """Resultados con símbolo, nombre y tipo; los demás (noticias, índices sin tipo) se omiten."""
    quotes: list[Quote] = []
    for raw in payload.get("quotes") or []:
        if not isinstance(raw, dict):
            continue
        symbol, kind = raw.get("symbol"), raw.get("quoteType")
        name = raw.get("longname") or raw.get("shortname")
        if isinstance(symbol, str) and isinstance(kind, str) and isinstance(name, str):
            quotes.append(Quote(symbol=symbol, name=name.strip(), quote_type=kind.upper()))
    return quotes


class YahooClient:
    def __init__(self, http: httpx.Client | None = None) -> None:
        self._http = http or httpx.Client(
            timeout=TIMEOUT_S,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
        )

    def chart(self, symbol: str, range_: str) -> Chart:
        """Cierres diarios de `range_` (`5d`, `3y`…) y último precio de `symbol`."""
        try:
            response = self._http.get(
                CHART_URL.format(symbol=symbol), params={"range": range_, "interval": "1d"}
            )
            response.raise_for_status()
            payload = response.json(parse_float=Decimal, parse_int=Decimal)
        except (httpx.HTTPError, ValueError) as error:
            raise ProviderError(f"{symbol}: {error}") from error
        if not isinstance(payload, dict):
            raise ProviderError(f"{symbol}: respuesta no válida")
        return parse_chart(payload, clock.now())

    def search(self, query: str) -> list[Quote]:
        """Busca por ISIN, ticker o nombre (T4-07). Lista vacía si Yahoo no conoce nada."""
        try:
            response = self._http.get(
                SEARCH_URL, params={"q": query, "quotesCount": 6, "newsCount": 0}
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise ProviderError(f"búsqueda «{query}»: {error}") from error
        if not isinstance(payload, dict):
            raise ProviderError(f"búsqueda «{query}»: respuesta no válida")
        return parse_search(payload)
