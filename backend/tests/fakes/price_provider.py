"""Proveedor de precios en memoria para los tests (sin ficheros ni red).

Uso:
    provider = FakePriceProvider(
        closes={"IE00B4L5Y983": {"2026-11-05": "95.10", "2026-11-06": "95.42"}},
        fx={"EURUSD": {"2026-11-06": "1.16"}},
    )
    with use_price_provider(provider):
        prices.service.latest("IE00B4L5Y983")
"""

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import date
from decimal import Decimal

from app.prices import service
from app.prices.provider import PricePoint

Series = Mapping[str, str | Decimal]
"""`{"AAAA-MM-DD": valor}`."""


def _points(series: Series) -> list[PricePoint]:
    return sorted(
        (PricePoint(day=date.fromisoformat(d), value=Decimal(str(v))) for d, v in series.items()),
        key=lambda p: p.day,
    )


class FakePriceProvider:
    def __init__(
        self,
        closes: Mapping[str, Series] | None = None,
        fx: Mapping[str, Series] | None = None,
    ) -> None:
        self._closes = {k: _points(v) for k, v in (closes or {}).items()}
        self._fx = {k: _points(v) for k, v in (fx or {}).items()}

    def closes(self, asset_id: str) -> list[PricePoint]:
        return list(self._closes.get(asset_id, []))

    def fx_closes(self, pair: str) -> list[PricePoint]:
        return list(self._fx.get(pair, []))


@contextmanager
def use_price_provider(provider: FakePriceProvider) -> Iterator[FakePriceProvider]:
    """Activa `provider` en `prices.service` y restaura el anterior al salir."""
    previous = service.set_provider(provider)
    try:
        yield provider
    finally:
        service.set_provider(previous)
