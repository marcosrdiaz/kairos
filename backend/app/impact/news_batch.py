"""Impacto de varias noticias en una cartera (T4-30): series de cierres, caché del día y traza.

`service.estimate_news_impacts` carga el contexto de la cartera una vez y llama aquí. Cada
resultado deja su traza una sola vez al día por cartera, noticia y posiciones (caché en memoria),
para que consultar la pantalla cada minuto no llene `calc_trace`.
"""

from collections.abc import Callable, Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any, cast

from app.core import trace
from app.impact import engine, news_estimate, news_flow
from app.prices import service as prices_service
from app.schemas.common import SourceRef, TraceKind
from app.schemas.news import NewsChannel, NewsEstimateOut, NewsEstimateStatus
from app.schemas.portfolio import PositionOut

NewsImpact = tuple[NewsEstimateOut, list[str]]
"""Estimación y posiciones afectadas."""

_CACHE: dict[tuple[object, ...], NewsImpact] = {}
_CACHE_MAX = 5000


def clear_cache() -> None:
    _CACHE.clear()


class _Series:
    """Cierres de factores y empresas, leídos una vez por petición."""

    def __init__(self) -> None:
        self._loaded: dict[str, news_estimate.Series] = {}

    def get(self, channel: NewsChannel, assets: Mapping[str, str]) -> news_estimate.Series:
        key = channel.factor.value if channel.factor else f"company:{channel.company_key}"
        if key not in self._loaded:
            if channel.factor is not None:
                points = prices_service.factor_closes(channel.factor)
            else:
                points = prices_service.beta_closes(assets[cast(str, channel.company_key)])
            self._loaded[key] = [(p.day, p.value) for p in points]
        return self._loaded[key]


def _series_for(
    series: _Series, request: news_flow.NewsImpactRequest
) -> Callable[[NewsChannel], news_estimate.Series]:
    return lambda channel: series.get(channel, request.company_assets)


def estimate_all(
    portfolio_id: str,
    requests: Sequence[news_flow.NewsImpactRequest],
    *,
    valued_positions: Sequence[PositionOut],
    positions: Sequence[engine.PositionIn],
    coverage: Decimal,
    total_eur: Decimal,
    trace_inputs: Mapping[str, Any],
    sources: Sequence[SourceRef],
    parent_calc_ids: Sequence[str],
    now: datetime,
) -> dict[str, NewsImpact]:
    info = {
        p.asset_id: news_flow.PositionInfo(p.price_kind, p.asset_type) for p in valued_positions
    }
    fingerprint = tuple(sorted((p.asset_id, str(p.units)) for p in valued_positions))
    series = _Series()
    results: dict[str, NewsImpact] = {}
    for request in requests:
        channels = tuple(
            sorted(f"{c.factor}|{c.company_key}|{c.direction}" for c in request.channels)
        )
        key = (portfolio_id, request.news_id, fingerprint, now.date(), channels)
        if key not in _CACHE:
            draft = news_flow.estimate(
                request, positions, info, coverage, total_eur, _series_for(series, request), now
            )
            estimate = draft.estimate
            if estimate.calc_id is not None:
                measured = estimate.status is NewsEstimateStatus.MEASURED
                calc_id = trace.record(
                    TraceKind.EVENT_IMPACT if measured else TraceKind.SCENARIO,
                    draft.formula,
                    inputs={**trace_inputs, **draft.trace_inputs},
                    outputs=estimate.model_dump(mode="json", exclude={"calc_id"}),
                    sources=[*draft.sources, *sources],
                    parent_calc_ids=list(parent_calc_ids),
                )
                estimate = estimate.model_copy(update={"calc_id": calc_id})
            if len(_CACHE) >= _CACHE_MAX:
                _CACHE.clear()
            _CACHE[key] = (estimate, draft.asset_ids)
        results[request.news_id] = _CACHE[key]
    return results
