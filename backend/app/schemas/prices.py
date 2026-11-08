"""Contrato de `prices` (diseño del MVP §4.1): lo que devuelven `latest()` y `history()`.

Es una interfaz Python entre módulos, sin endpoint propio. Ejemplo en
`schemas/examples/PriceOut.json`.
"""

from app.schemas.common import ContractModel, Price, PriceKind, SourceRef, UtcDatetime


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
