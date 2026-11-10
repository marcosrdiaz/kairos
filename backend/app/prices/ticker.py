"""Variación de precio del ticker de mercado (T2-17). Función pura: sin BD ni proveedor.

La usa `prices.service.ticker_item`, que añade los precios y la traza.
"""

from decimal import ROUND_HALF_EVEN, Decimal

CHANGE_STEP = Decimal("0.000001")
"""Precisión de `change_pct`: fracción con 6 decimales (0,0001 %)."""

FORMULA = "change_pct = (price - previous_price) / previous_price"


def change_pct(price: Decimal, previous: Decimal | None) -> Decimal | None:
    """Variación de `price` frente a `previous`, como fracción. `None` si no hay precio anterior
    o es cero (no se puede dividir)."""
    if previous is None or previous == 0:
        return None
    return ((price - previous) / previous).quantize(CHANGE_STEP, rounding=ROUND_HALF_EVEN)
