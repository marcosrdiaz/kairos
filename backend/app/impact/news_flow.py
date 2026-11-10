"""Impacto de una noticia en una cartera (T4-30): de los canales de la clasificación al rango en €.

Usa el mismo motor que los eventos y los escenarios (`engine.compute_impact`) con los shocks de
`news_estimate` (medidos o estimados con datos). El LLM no pone ningún número: solo elige los
canales y su dirección. Ver `news_estimate.py` y la decisión «Impacto de una noticia…».
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from app.impact import engine, news_estimate
from app.schemas.common import (
    AssetType,
    Confidence,
    Factor,
    Polarity,
    PriceKind,
    SourceKind,
    SourceRef,
)
from app.schemas.news import (
    NewsChannel,
    NewsEstimateMethod,
    NewsEstimateOut,
    NewsEstimateStatus,
    NewsPositionEstimate,
)

ABSOLUTE_FACTORS = frozenset({Factor.RATES_EUR})
_PCT = Decimal("0.0001")
_CENT = Decimal("0.01")
_ZERO = Decimal("0")

FORMULA_MEASURED = (
    "Impacto de la noticia = motor de impacto con el movimiento real de cada canal (factor o "
    "empresa elegidos por la clasificación) en la sesión que la recoge, frente al cierre "
    "anterior. Incluye todo lo que movió el mercado esa sesión."
)
FORMULA_ESTIMATED = (
    "Impacto estimado = motor de impacto con, para cada canal, la dirección de la clasificación "
    "y el tamaño del movimiento a cinco sesiones en los días de noticia fuerte de los últimos "
    "tres años (percentiles 25, 50 y 75). Rango = suma de los extremos de cada canal más la "
    "incertidumbre de las betas."
)


@dataclass(frozen=True)
class NewsImpactRequest:
    news_id: str
    title: str
    url: str | None
    published_at: datetime
    channels: Sequence[NewsChannel]
    company_assets: Mapping[str, str] = field(default_factory=dict)
    """Clave de empresa → `asset_id` con precios (para su serie de cierres)."""


@dataclass(frozen=True)
class NewsImpactDraft:
    """Resultado sin `calc_id` todavía; `trace_inputs` va a la traza."""

    estimate: NewsEstimateOut
    asset_ids: list[str]
    trace_inputs: dict[str, object]
    sources: list[SourceRef]
    formula: str


@dataclass(frozen=True)
class PositionInfo:
    price_kind: PriceKind
    asset_type: AssetType


SeriesFor = Callable[[NewsChannel], news_estimate.Series]


def _key(channel: NewsChannel) -> str:
    return channel.factor.value if channel.factor else f"company:{channel.company_key}"


def _shocks_in(values: Mapping[str, Decimal]) -> engine.ShocksIn:
    factors = {Factor(k): v for k, v in values.items() if not k.startswith("company:")}
    companies = {
        k.removeprefix("company:"): v for k, v in values.items() if k.startswith("company:")
    }
    return engine.ShocksIn(factors, companies, {})


def _channel_shocks(
    request: NewsImpactRequest, series_for: SeriesFor, today: date
) -> tuple[dict[str, tuple[Decimal, Decimal, Decimal]], bool, int | None, date]:
    """Shocks `(bajo, central, alto)` por canal, si son medidos, días de noticia y sesión."""
    session = news_estimate.reaction_session(request.published_at)
    usable = [c for c in request.channels if c.factor or c.company_key in request.company_assets]
    if session < today:
        measured: dict[str, tuple[Decimal, Decimal, Decimal]] = {}
        for channel in usable:
            absolute = channel.factor in ABSOLUTE_FACTORS
            move = news_estimate.session_move(series_for(channel), session, absolute)
            if move is None:
                break
            measured[_key(channel)] = (move, move, move)
        else:
            if measured:
                return measured, True, None, session
    estimated: dict[str, tuple[Decimal, Decimal, Decimal]] = {}
    days: list[int] = []
    for channel in usable:
        absolute = channel.factor in ABSOLUTE_FACTORS
        band = news_estimate.move_band(series_for(channel), today, absolute=absolute)
        if band is not None:
            estimated[_key(channel)] = news_estimate.signed_shocks(channel.direction, band)
            days.append(band.n)
    return estimated, False, (min(days) if days else None), session


def _cents(value: Decimal) -> Decimal:
    return value.quantize(_CENT)


def _empty(status: NewsEstimateStatus, now: datetime) -> NewsEstimateOut:
    return NewsEstimateOut(status=status, as_of=now)


def estimate(
    request: NewsImpactRequest,
    positions: Sequence[engine.PositionIn],
    info: Mapping[str, PositionInfo],
    coverage: Decimal,
    total_eur: Decimal,
    series_for: SeriesFor,
    now: datetime,
) -> NewsImpactDraft:
    """Impacto de la noticia en las posiciones dadas. Sin canales utilizables: `pending`; sin
    ninguna posición afectada: `not_relevant`."""
    shocks, measured, days, session = _channel_shocks(request, series_for, now.date())
    if not request.channels:
        return NewsImpactDraft(_empty(NewsEstimateStatus.NOT_RELEVANT, now), [], {}, [], "")
    if not shocks:
        return NewsImpactDraft(_empty(NewsEstimateStatus.PENDING, now), [], {}, [], "")

    central = engine.compute_impact(
        positions, _shocks_in({k: mid for k, (_, mid, _) in shocks.items()}), coverage
    )
    total_low = central.low_eur - central.impact_eur
    total_high = central.high_eur - central.impact_eur
    asset_low = {a.asset_id: (a.low_eur or a.impact_eur) - a.impact_eur for a in central.assets}
    asset_high = {a.asset_id: (a.high_eur or a.impact_eur) - a.impact_eur for a in central.assets}
    if measured:
        total_low += central.impact_eur
        total_high += central.impact_eur
        for a in central.assets:
            asset_low[a.asset_id] += a.impact_eur
            asset_high[a.asset_id] += a.impact_eur
    else:
        for key, (low, _, high) in shocks.items():
            ends = [
                engine.compute_impact(positions, _shocks_in({key: v}), coverage)
                for v in (low, high)
            ]
            total_low += min(r.impact_eur for r in ends)
            total_high += max(r.impact_eur for r in ends)
            for at_low, at_high in zip(ends[0].assets, ends[1].assets, strict=True):
                asset_low[at_low.asset_id] += min(at_low.impact_eur, at_high.impact_eur)
                asset_high[at_low.asset_id] += max(at_low.impact_eur, at_high.impact_eur)

    impact = central.impact_eur
    low, high = _cents(min(total_low, impact)), _cents(max(total_high, impact))
    rows: list[NewsPositionEstimate] = []
    for a in central.assets:
        a_low = _cents(min(asset_low[a.asset_id], a.impact_eur))
        a_high = _cents(max(asset_high[a.asset_id], a.impact_eur))
        if max(abs(a_low), abs(a_high)) < _CENT:
            continue
        position = info[a.asset_id]
        timing, effective = news_estimate.effect_timing(
            position.price_kind, position.asset_type, session
        )
        rows.append(
            NewsPositionEstimate(
                asset_id=a.asset_id,
                name=a.name,
                impact_eur=a.impact_eur,
                low_eur=a_low,
                high_eur=a_high,
                timing=timing,
                effective_from=effective,
            )
        )
    if not rows:
        return NewsImpactDraft(_empty(NewsEstimateStatus.NOT_RELEVANT, now), [], {}, [], "")

    confidence = central.confidence
    if not measured and confidence is Confidence.ALTA:
        confidence = Confidence.MEDIA  # una estimación nunca sale con confianza alta

    def pct(value: Decimal) -> Decimal:
        return (value / total_eur).quantize(_PCT) if total_eur else _ZERO

    polarity = (
        Polarity.RIESGO if impact < 0 else Polarity.OPORTUNIDAD if impact > 0 else Polarity.NEUTRAL
    )
    out = NewsEstimateOut(
        status=NewsEstimateStatus.MEASURED if measured else NewsEstimateStatus.ESTIMATED,
        polarity=polarity,
        impact_eur=impact,
        low_eur=low,
        high_eur=high,
        impact_pct=pct(impact),
        low_pct=pct(low),
        high_pct=pct(high),
        horizon_sessions=1 if measured else news_estimate.HORIZON_SESSIONS,
        confidence=confidence,
        method=NewsEstimateMethod.MEASURED if measured else NewsEstimateMethod.VOLATILITY,
        analogs_count=days,
        positions=rows,
        calc_id="pending",
        event_id=None,
        as_of=now,
    )
    sources = [
        SourceRef(
            kind=SourceKind.EVENT,
            label=f"Noticia: {request.title[:120]}",
            ref=request.news_id,
            as_of=request.published_at,
            url=request.url,
        ),
        *(
            SourceRef(kind=SourceKind.PRICE, label=f"Cierres de {key}", ref=key)
            for key in sorted(shocks)
        ),
    ]
    trace_inputs: dict[str, object] = {
        "session": session.isoformat(),
        "mode": "measured" if measured else "estimated",
        "shocks": {k: {"low": lo, "mid": mid, "high": hi} for k, (lo, mid, hi) in shocks.items()},
        "news_days": days,
        "horizon_sessions": out.horizon_sessions,
        "r2_weighted": central.r2,
    }
    formula = FORMULA_MEASURED if measured else FORMULA_ESTIMATED
    return NewsImpactDraft(out, [r.asset_id for r in rows], trace_inputs, sources, formula)
