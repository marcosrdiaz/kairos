"""Contrato de `prices` (diseño del MVP §4.1): lo que devuelven `latest()` y `history()`, y el
ticker de mercado de Inicio (T2-17).

`PriceOut` es una interfaz Python entre módulos, sin endpoint propio. `TickerOut` es la respuesta
de `GET /portfolios/{id}/ticker`. Ejemplos en `schemas/examples/PriceOut.json` y `TickerOut.json`.
"""

from app.schemas.common import ContractModel, Fraction, Price, PriceKind, SourceRef, UtcDatetime


class PriceOut(ContractModel):
    """Precio de un activo en un instante, en la divisa del activo (`currency`).

    `price_at` es el instante del dato (cierre, VL o cotización), no el de la consulta.
    `source` va a la traza de quien use el precio (`SourceRef.kind = "price"`).
    """

    asset_id: str
    price: Price
    currency: str
    price_at: UtcDatetime
    price_kind: PriceKind
    source: SourceRef


class TickerItemOut(ContractModel):
    """Un activo de la cartera en el ticker: último precio y variación frente al cierre anterior.

    `change_pct` es una fracción (`"-0.0123"` = −1,23 %) y la calcula el backend:
    `(price - previous_price) / previous_price`. Es `null` si no hay cierre anterior o si el precio
    es fijo (depósito, plan de pensiones). `calc_id` apunta a la traza con los dos precios y sus
    fuentes.
    """

    asset_id: str
    ticker: str | None
    name: str
    price: Price
    currency: str
    price_at: UtcDatetime
    price_kind: PriceKind
    previous_price: Price | None
    previous_price_at: UtcDatetime | None
    change_pct: Fraction | None
    source: SourceRef
    calc_id: str


class TickerOut(ContractModel):
    """Respuesta de `GET /portfolios/{id}/ticker`: un elemento por posición, en el orden de la
    cartera. `as_of` es el instante de la consulta (`clock.now()`)."""

    portfolio_id: str
    as_of: UtcDatetime
    items: list[TickerItemOut]
