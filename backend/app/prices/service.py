"""Interfaz pública de `prices` (diseño del MVP §4.1). Lo único que importan otros módulos.

- `latest(asset_id)`: último cierre (o VL) con fecha no posterior a `clock.now()`.
- `history(asset_id, start, end)`: cierres entre dos fechas, ambas incluidas.
- `previous_close(asset_id, day)`: último cierre anterior a `day` (`None` con precio fijo).
- `ticker_item(asset_id, ticker, name)`: último precio y variación frente al cierre anterior,
  con traza (ticker de Inicio, T2-17).
- `fx_rate(pair, at)`: tipo `EURUSD` (dólares por euro), el inverso `USDEUR` o `1` si la divisa es
  la misma. `fx_quote` devuelve además el instante y la fuente para la traza.

Los precios offline son cierres diarios: `price_at` es la fecha del cierre a las 00:00 UTC.
Un precio `fixed:<valor>` vale lo mismo cualquier día; su `price_at` es el día de `clock.now()`.
Con `MARKET_DATA_PROVIDER` distinto de `offline` se usa también el offline mientras no haya
proveedor en directo (D-026).
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from app.core import clock, trace
from app.core.errors import AppError, ErrorCode
from app.prices.catalog import AssetPriceSpec, load_catalog
from app.prices.provider import OfflineCsvProvider, PricePoint, PriceProvider
from app.prices.ticker import FORMULA as CHANGE_FORMULA
from app.prices.ticker import change_pct
from app.schemas.common import PriceKind, SourceKind, SourceRef, TraceKind
from app.schemas.prices import PriceOut, TickerItemOut

_FX_STEP = Decimal("0.00000001")

_provider: PriceProvider | None = None


def get_provider() -> PriceProvider:
    global _provider
    if _provider is None:
        _provider = OfflineCsvProvider()
    return _provider


def set_provider(provider: PriceProvider | None) -> PriceProvider | None:
    """Cambia el proveedor (tests, proveedor en directo). `None` vuelve al offline por defecto.
    Devuelve el anterior para poder restaurarlo."""
    global _provider
    previous, _provider = _provider, provider
    return previous


# --- Precios ---


def _spec(asset_id: str) -> AssetPriceSpec:
    spec = load_catalog().get(asset_id)
    if spec is None:
        raise AppError(
            ErrorCode.NOT_FOUND,
            f"No conocemos el activo «{asset_id}».",
            details={"asset_id": asset_id},
        )
    return spec


def _midnight(day: date) -> datetime:
    return datetime.combine(day, time(), tzinfo=UTC)


def _to_out(spec: AssetPriceSpec, point: PricePoint) -> PriceOut:
    at = _midnight(point.day)
    if spec.fixed_price is not None:
        label = f"Valor fijo de {spec.name}"
    elif spec.price_kind is PriceKind.NAV_DAILY:
        label = f"VL de {spec.name}"
    else:
        label = f"Cierre de {spec.name}"
    return PriceOut(
        asset_id=spec.asset_id,
        price=point.value,
        currency=spec.currency,
        price_at=at,
        price_kind=spec.price_kind,
        source=SourceRef(kind=SourceKind.PRICE, label=label, ref=spec.asset_id, as_of=at),
    )


def _unavailable(asset_id: str, at: datetime) -> AppError:
    return AppError(
        ErrorCode.PRICE_UNAVAILABLE,
        "No hay precio disponible para este activo en esa fecha.",
        details={"asset_id": asset_id, "at": at.isoformat()},
    )


def latest(asset_id: str) -> PriceOut:
    spec = _spec(asset_id)
    now = clock.now()
    if spec.fixed_price is not None:
        return _to_out(spec, PricePoint(day=now.date(), value=spec.fixed_price))
    known = [p for p in get_provider().closes(asset_id) if p.day <= now.date()]
    if not known:
        raise _unavailable(asset_id, now)
    return _to_out(spec, known[-1])


def history(asset_id: str, start: date, end: date) -> list[PriceOut]:
    spec = _spec(asset_id)
    if spec.fixed_price is not None:
        days = (start + timedelta(days=n) for n in range((end - start).days + 1))
        return [_to_out(spec, PricePoint(day=d, value=spec.fixed_price)) for d in days]
    points = get_provider().closes(asset_id)
    return [_to_out(spec, p) for p in points if start <= p.day <= end]


def previous_close(asset_id: str, day: date) -> PriceOut | None:
    """Último cierre (o VL) anterior a `day`. `None` si no hay o si el precio es fijo."""
    spec = _spec(asset_id)
    if spec.fixed_price is not None:
        return None
    before = [p for p in get_provider().closes(asset_id) if p.day < day]
    return _to_out(spec, before[-1]) if before else None


# --- Ticker de mercado (T2-17) ---


def ticker_item(asset_id: str, ticker: str | None, name: str) -> TickerItemOut:
    """Último precio de un activo y su variación frente al cierre anterior, con traza."""
    last = latest(asset_id)
    previous = previous_close(asset_id, last.price_at.date())
    previous_price = previous.price if previous else None
    change = change_pct(last.price, previous_price)
    if change is None:
        formula = "Sin cierre anterior comparable: no se calcula la variación"
    else:
        formula = CHANGE_FORMULA
    calc_id = trace.record(
        TraceKind.VALUATION,
        formula,
        inputs={
            "asset_id": asset_id,
            "price": last.price,
            "price_at": last.price_at,
            "previous_price": previous_price,
            "previous_price_at": previous.price_at if previous else None,
        },
        outputs={"change_pct": change},
        sources=[last.source] + ([previous.source] if previous else []),
    )
    return TickerItemOut(
        asset_id=asset_id,
        ticker=ticker,
        name=name,
        price=last.price,
        currency=last.currency,
        price_at=last.price_at,
        price_kind=last.price_kind,
        previous_price=previous_price,
        previous_price_at=previous.price_at if previous else None,
        change_pct=change,
        source=last.source,
        calc_id=calc_id,
    )


# --- Tipos de cambio ---


@dataclass(frozen=True)
class FxQuote:
    pair: str
    rate: Decimal
    """Unidades de la segunda divisa por una de la primera: `USDEUR` 0.8621 = 1 USD son 0,8621 €."""
    at: datetime
    source: SourceRef


def _check_pair(pair: str) -> tuple[str, str]:
    if len(pair) != 6 or not pair.isalpha() or not pair.isupper():
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            f"Par de divisas no válido: «{pair}».",
            details={"pair": pair},
        )
    return pair[:3], pair[3:]


def _last_until(points: list[PricePoint], day: date) -> PricePoint | None:
    known = [p for p in points if p.day <= day]
    return known[-1] if known else None


def fx_quote(pair: str, at: datetime | None = None) -> FxQuote:
    base, quote = _check_pair(pair)
    when = at or clock.now()
    if base == quote:
        source = SourceRef(kind=SourceKind.FX, label="Misma divisa", ref=pair, as_of=None)
        return FxQuote(pair=pair, rate=Decimal(1), at=when, source=source)
    provider = get_provider()
    direct = _last_until(provider.fx_closes(pair), when.date())
    if direct is not None:
        stored, rate = pair, direct.value
        point = direct
    else:
        inverse = _last_until(provider.fx_closes(quote + base), when.date())
        if inverse is None:
            raise AppError(
                ErrorCode.PRICE_UNAVAILABLE,
                "No hay tipo de cambio disponible para esa fecha.",
                details={"pair": pair, "at": when.isoformat()},
            )
        stored, rate = quote + base, (Decimal(1) / inverse.value).quantize(_FX_STEP)
        point = inverse
    as_of = _midnight(point.day)
    source = SourceRef(
        kind=SourceKind.FX,
        label=f"Tipo de cambio {stored[:3]}/{stored[3:]}",
        ref=stored,
        as_of=as_of,
    )
    return FxQuote(pair=pair, rate=rate, at=as_of, source=source)


def fx_rate(pair: str, at: datetime | None = None) -> Decimal:
    return fx_quote(pair, at).rate
