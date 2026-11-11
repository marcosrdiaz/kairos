"""Interfaz pública del estado del widget (diseño del MVP §4.2, `SPEC.md` §8.6).

El estado se guarda calculado en memoria, por cartera, para que `GET /status` responda en menos de
200 ms. `recompute` (tras cada evento) redacta la frase con el modelo. `get_status` nunca llama al
modelo: cada `config.REFRESH_S` comprueba si han cambiado los datos y, si es así, usa la plantilla.
El `calc_id` solo cambia si cambian los datos; `agents/context.py` depende de eso.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime
from threading import Lock

from app.core import clock, trace
from app.core.errors import AppError
from app.impact import service as impact_service
from app.portfolio import service as portfolio_service
from app.prices import service as prices_service
from app.schemas.agents import (
    SentenceStatus,
    StatusFacts,
    StatusFactsReason,
    StatusReasonKind,
    StatusState,
)
from app.schemas.common import SourceRef, TraceKind
from app.schemas.impact import EventImpactOut
from app.schemas.portfolio import PlanOut, PortfolioOut
from app.schemas.status import StatusOut, StatusReason
from app.status import config, engine

_SentenceWriter = Callable[[StatusFacts], tuple[str, SentenceStatus]]


@dataclass(frozen=True)
class _Reading:
    """Lo leído de los otros módulos. `facts` aún sin `calc_id`: la traza se crea si hay cambios."""

    facts: StatusFacts
    price_as_of: datetime
    parent_calc_ids: list[str]
    sources: list[SourceRef]


@dataclass(frozen=True)
class _Snapshot:
    facts: StatusFacts
    price_as_of: datetime
    status: StatusOut
    checked_at: float

    def matches(self, reading: _Reading) -> bool:
        return self.facts == reading.facts and self.price_as_of == reading.price_as_of


_snapshots: dict[str, _Snapshot] = {}
_lock = Lock()
_monotonic = time.monotonic  # reloj del refresco; los tests lo sustituyen


def _optional_plan(portfolio_id: str) -> PlanOut | None:
    try:
        return portfolio_service.get_plan(portfolio_id)
    except AppError:
        return None


def _price_as_of(portfolio: PortfolioOut) -> datetime:
    """Fecha del último precio de mercado de la cartera. Los activos de valor fijo (depósitos,
    planes) no cuentan: su «precio» lleva la fecha del reloj, no la de una cotización."""
    market = [
        p.price_at for p in portfolio.positions if prices_service.has_market_prices(p.asset_id)
    ]
    return max(market, default=portfolio.valued_at)


def _main_channel(event: EventImpactOut) -> str | None:
    top = max(event.breakdown, key=lambda asset: abs(asset.impact_eur), default=None)
    return top.channel if top else None


def _facts(
    portfolio: PortfolioOut, state: StatusState, event: EventImpactOut | None, plan: PlanOut | None
) -> StatusFacts:
    facts = StatusFacts(
        state=state,
        total_eur=portfolio.total_eur,
        change_week_pct=portfolio.change_week_pct,
        reason=StatusFactsReason(kind=StatusReasonKind.NONE, event_id=None),
        calc_id="",
    )
    if event is not None:
        return facts.model_copy(
            update={
                "reason": StatusFactsReason(kind=StatusReasonKind.EVENT, event_id=event.event_id),
                "event_title": event.title,
                "main_channel": _main_channel(event),
                "event_impact_eur": event.impact_eur,
            }
        )
    if state is StatusState.REVISA_PLAN and plan is not None:
        return facts.model_copy(
            update={
                "reason": StatusFactsReason(kind=StatusReasonKind.DRIFT, event_id=None),
                "equity_current": plan.current.equity,
                "equity_target": plan.target.equity,
            }
        )
    return facts


def _read(portfolio_id: str) -> _Reading:
    portfolio = portfolio_service.get_valued(portfolio_id)
    plan = _optional_plan(portfolio_id)
    impacts = impact_service.list_event_impacts(portfolio_id, config.ATENTO_WINDOW.days)
    state, event = engine.evaluate(
        portfolio.total_eur,
        impacts,
        drift_exceeded=plan is not None and plan.drift_exceeded,
        now=clock.now(),
    )
    parents = [portfolio.calc_id]
    if plan is not None:
        parents.append(plan.calc_id)
    if event is not None:
        parents.append(event.calc_id)
    return _Reading(
        _facts(portfolio, state, event, plan),
        _price_as_of(portfolio),
        parents,
        list(event.sources) if event is not None else [],
    )


def _record(portfolio_id: str, reading: _Reading) -> str:
    facts = reading.facts
    return trace.record(
        TraceKind.STATUS,
        engine.FORMULA,
        inputs={
            "portfolio_id": portfolio_id,
            "total_eur": facts.total_eur,
            "event_impact_eur": facts.event_impact_eur,
            "equity_current": facts.equity_current,
            "equity_target": facts.equity_target,
        },
        outputs={
            "state": facts.state,
            "reason_kind": facts.reason.kind,
            "event_id": facts.reason.event_id,
        },
        sources=reading.sources,
        parent_calc_ids=reading.parent_calc_ids,
    )


def _status(
    facts: StatusFacts, price_as_of: datetime, sentence: str, written: SentenceStatus
) -> StatusOut:
    return StatusOut(
        state=facts.state,
        state_label=config.LABELS[facts.state],
        total_eur=facts.total_eur,
        change_week_pct=facts.change_week_pct,
        sentence=sentence,
        sentence_status=written,
        reason=StatusReason(
            kind=facts.reason.kind,
            event_id=facts.reason.event_id,
            event_impact_eur=facts.event_impact_eur,
        ),
        price_as_of=price_as_of,
        computed_at=clock.now(),
        calc_id=facts.calc_id,
    )


def _store(
    portfolio_id: str, reading: _Reading, checked_at: float, write_sentence: _SentenceWriter
) -> StatusOut:
    facts = reading.facts.model_copy(update={"calc_id": _record(portfolio_id, reading)})
    sentence, written = write_sentence(facts)
    status = _status(facts, reading.price_as_of, sentence, written)
    snapshot = _Snapshot(reading.facts, reading.price_as_of, status, checked_at)
    with _lock:
        _snapshots[portfolio_id] = snapshot
    return status


def _keep(portfolio_id: str, snapshot: _Snapshot, checked_at: float) -> StatusOut:
    with _lock:
        _snapshots[portfolio_id] = replace(snapshot, checked_at=checked_at)
    return snapshot.status


def _sentence(facts: StatusFacts, *, use_model: bool) -> tuple[str, SentenceStatus]:
    from app.agents import service as agents_service  # aquí por el ciclo agents → status → agents

    return agents_service.write_status_sentence(facts, use_model=use_model)


def _template_sentence(facts: StatusFacts) -> tuple[str, SentenceStatus]:
    return _sentence(facts, use_model=False)


def _model_sentence(facts: StatusFacts) -> tuple[str, SentenceStatus]:
    return _sentence(facts, use_model=True)


def get_status(portfolio_id: str) -> StatusOut:
    """Lee lo precalculado. Sin modelo, para responder en menos de 200 ms. 404 si no existe."""
    now = _monotonic()
    with _lock:
        snapshot = _snapshots.get(portfolio_id)
    if snapshot is not None and now - snapshot.checked_at < config.REFRESH_S:
        return snapshot.status
    reading = _read(portfolio_id)
    if snapshot is not None and snapshot.matches(reading):
        return _keep(portfolio_id, snapshot, now)
    return _store(portfolio_id, reading, now, _template_sentence)


def recompute(portfolio_id: str) -> StatusOut:
    """Recalcula tras un evento. Si no cambia nada y la frase ya es del modelo, no la reescribe."""
    now = _monotonic()
    with _lock:
        snapshot = _snapshots.get(portfolio_id)
    reading = _read(portfolio_id)
    if (
        snapshot is not None
        and snapshot.matches(reading)
        and snapshot.status.sentence_status is SentenceStatus.OK
    ):
        return _keep(portfolio_id, snapshot, now)
    return _store(portfolio_id, reading, now, _model_sentence)


def reset() -> None:
    """Olvida los estados calculados (`/demo/reset`)."""
    with _lock:
        _snapshots.clear()
