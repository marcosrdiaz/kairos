"""Interfaz pública de `alerts` (diseño del MVP §4.4, D-032).

`evaluate` lo llama `events` tras cada impacto: un evento genera como máximo un aviso
`event_impact` por cartera, solo si `score >= 1` y queda cupo en la semana ISO.
"""

from decimal import ROUND_HALF_EVEN, Decimal
from threading import Lock

from app.agents import service as agents_service
from app.alerts import config, engine, repository
from app.core import clock
from app.impact import service as impact_service
from app.portfolio import service as portfolio_service
from app.schemas.agents import EventImpactStub
from app.schemas.alerts import AlertKind, AlertOut
from app.schemas.impact import EventImpactOut

_SCORE_STEP = Decimal("0.0001")
_lock = Lock()  # comprobar-y-guardar sin que dos replays seguidos dupliquen el aviso


def _impact_of(portfolio_id: str, event_id: str) -> EventImpactOut | None:
    impacts = impact_service.list_event_impacts(portfolio_id, config.IMPACT_LOOKBACK_DAYS)
    return next((i for i in impacts if i.event_id == event_id), None)


def evaluate(portfolio_id: str, event_id: str) -> None:
    """Decide si un evento genera aviso y, si procede, lo redacta (guardián) y lo guarda."""
    impact = _impact_of(portfolio_id, event_id)
    if impact is None:
        return
    total_eur = portfolio_service.get_valued(portfolio_id).total_eur  # mismo total que `status`
    if not engine.is_significant(impact.impact_eur, total_eur):
        return
    with _lock:
        if repository.exists(portfolio_id, event_id, AlertKind.EVENT_IMPACT):
            return  # idempotente: repetir el replay no duplica ni gasta cupo
        now = clock.now()
        start, end = engine.iso_week_bounds(now)
        if not engine.within_weekly_limit(repository.count_between(portfolio_id, start, end)):
            return
        stub = EventImpactStub.model_validate(
            impact.model_dump(mode="json", include=set(EventImpactStub.model_fields))
        )
        repository.save(
            portfolio_id,
            event_id,
            AlertKind.EVENT_IMPACT,
            engine.score(impact.impact_eur, total_eur).quantize(
                _SCORE_STEP, rounding=ROUND_HALF_EVEN
            ),
            agents_service.write_alert_message(stub),
            now,
        )


def list_alerts(portfolio_id: str) -> list[AlertOut]:
    portfolio_service.ensure_exists(portfolio_id)  # NOT_FOUND si la cartera no existe
    calc_ids = {
        i.event_id: i.calc_id
        for i in impact_service.list_event_impacts(portfolio_id, config.IMPACT_LOOKBACK_DAYS)
    }
    return [
        AlertOut(
            id=a.id,
            event_id=a.event_id,
            kind=a.kind,
            score=a.score,
            message=a.message,
            created_at=a.created_at,
            delivered=a.delivered,
            calc_id=calc_ids.get(a.event_id) if a.event_id else None,
        )
        for a in repository.list_for(portfolio_id)
    ]
