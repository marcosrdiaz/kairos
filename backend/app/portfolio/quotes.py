"""Precio actual, fx y valor de hace 7 días de los activos, desde `prices.service`.

Lo usan la valoración y las operaciones. Lanza `PRICE_UNAVAILABLE` (503) si falta un precio.
"""

from collections.abc import Iterable
from datetime import datetime, timedelta
from decimal import Decimal

from app.core import clock
from app.core.errors import AppError
from app.portfolio import errors
from app.portfolio.engine import QuoteIn
from app.prices import service as prices
from app.schemas.common import SourceRef

WEEK = timedelta(days=7)


def quotes(asset_ids: Iterable[str]) -> tuple[dict[str, QuoteIn], list[SourceRef]]:
    """Precio actual, fx y valor unitario de hace 7 días de cada activo, con sus fuentes."""
    week_at = clock.now() - WEEK
    out: dict[str, QuoteIn] = {}
    sources: dict[tuple[str, str], SourceRef] = {}
    for asset_id in sorted(asset_ids):
        price = prices.latest(asset_id)
        pair = f"{price.currency}EUR"
        fx = prices.fx_quote(pair)
        sources.setdefault((price.source.kind, price.source.ref), price.source)
        if price.currency != "EUR":
            sources.setdefault((fx.source.kind, fx.source.ref), fx.source)
        out[asset_id] = QuoteIn(
            price=price.price,
            currency=price.currency,
            price_at=price.price_at,
            price_kind=price.price_kind,
            fx_rate=fx.rate,
            week_ago_unit_eur=_week_ago_unit_eur(asset_id, pair, week_at),
        )
    return out, list(sources.values())


def unit_eur_at(asset_id: str, at: datetime) -> tuple[Decimal, list[SourceRef]]:
    """`price × fx` del último cierre no posterior a `at` (como mucho 10 días antes), con sus
    fuentes. Lanza `PRICE_UNAVAILABLE` si no hay dato."""
    history = prices.history(asset_id, (at - timedelta(days=10)).date(), at.date())
    if not history:
        raise errors.price_unavailable_at(asset_id, at)
    close = history[-1]
    fx = prices.fx_quote(f"{close.currency}EUR", at)
    sources = [close.source] if close.currency == "EUR" else [close.source, fx.source]
    return close.price * fx.rate, sources


def _week_ago_unit_eur(asset_id: str, pair: str, at: datetime) -> Decimal | None:
    """`price × fx` del último cierre no posterior a `at`. `None` si no hay dato."""
    history = prices.history(asset_id, (at - timedelta(days=10)).date(), at.date())
    if not history:
        return None
    try:
        return history[-1].price * prices.fx_rate(pair, at)
    except AppError:
        return None
