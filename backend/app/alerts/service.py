"""Interfaz pública de `alerts` (diseño del MVP §4.4, D-032).

`evaluate` lo llama `events` tras cada impacto: un evento genera como máximo un aviso
`event_impact` por cartera, solo si `score >= 1` y queda cupo en la semana ISO.
"""

from datetime import datetime
from decimal import ROUND_HALF_EVEN, Decimal
from threading import Lock

from app.agents import service as agents_service
from app.alerts import config, engine, market_move, news_estimate, repository
from app.config import get_settings
from app.core import clock
from app.impact import service as impact_service
from app.news import service as news_service
from app.portfolio import service as portfolio_service
from app.schemas.agents import EventImpactStub
from app.schemas.alerts import AlertKind, AlertOut
from app.schemas.impact import EventImpactOut
from app.schemas.news import NewsEstimateStatus, NewsItemOut

_SCORE_STEP = Decimal("0.0001")
_lock = Lock()  # comprobar-y-guardar sin que dos replays seguidos dupliquen el aviso
_last_market_check: dict[str, datetime] = {}  # cartera → última comprobación de `market_move`
_last_news_check: dict[str, datetime] = {}  # cartera → última revisión de noticias (T4-31)


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


def reset() -> None:
    """Deja los avisos como al empezar la demo (`/demo/reset`): borra los que no tienen evento
    (`news_estimate`, `market_move`) y olvida cuándo se revisó cada cartera, para que los vuelva a
    generar solo lo que toque a partir del reloj de ese momento. Los de evento los borra
    `events.service.reset` por la clave foránea."""
    repository.delete_without_event()
    reset_market_move_checks()
    reset_news_checks()


def reset_market_move_checks() -> None:
    """Olvida cuándo se comprobó cada cartera (tests)."""
    with _lock:
        _last_market_check.clear()


def check_market_move(portfolio_id: str) -> None:
    """Aviso `market_move` (T2-21) si la cartera se ha movido hoy más que el umbral y ningún
    evento lo explica. Uno por cartera y día; comparte el límite semanal con `event_impact`.
    Se comprueba al leer los avisos, como mucho cada `MARKET_MOVE_CHECK_EVERY`."""
    if get_settings().demo_mode and not config.MARKET_MOVE_IN_DEMO:
        return  # no gasta el cupo que necesita el aviso del evento del guion
    now = clock.now()
    with _lock:
        last = _last_market_check.get(portfolio_id)
        if last is not None and last <= now < last + config.MARKET_MOVE_CHECK_EVERY:
            return
        _last_market_check[portfolio_id] = now
        if not _market_move_allowed(portfolio_id, now):
            return
    move = impact_service.explain_move(portfolio_id, "day")
    total_eur = portfolio_service.get_valued(portfolio_id).total_eur  # mismo total que `status`
    score = market_move.score_if_alert(move.change_eur, move.unexplained_eur, total_eur)
    if score is None:
        return
    message = agents_service.write_market_move_message(move)  # fuera del cerrojo: tarda
    with _lock:
        if not _market_move_allowed(portfolio_id, now):
            return  # otro aviso ha llegado mientras se redactaba
        repository.save(
            portfolio_id,
            None,
            AlertKind.MARKET_MOVE,
            score.quantize(_SCORE_STEP, rounding=ROUND_HALF_EVEN),
            message,
            now,
            calc_id=move.calc_id,
        )


def _market_move_allowed(portfolio_id: str, now: datetime) -> bool:
    """Sin aviso `market_move` hoy y con cupo en la semana ISO. Llamar con `_lock`."""
    if repository.exists_between(portfolio_id, AlertKind.MARKET_MOVE, *market_move.day_bounds(now)):
        return False
    week_start, week_end = engine.iso_week_bounds(now)
    return engine.within_weekly_limit(repository.count_between(portfolio_id, week_start, week_end))


def reset_news_checks() -> None:
    """Olvida cuándo se revisaron las noticias de cada cartera (tests)."""
    with _lock:
        _last_news_check.clear()


def check_news(portfolio_id: str, *, force: bool = False) -> int:
    """Avisos `news_estimate` (T4-31) de las noticias recientes que mueven la cartera más que su
    umbral según el perfil (`news_estimate.py`). Como mucho uno nuevo por cartera y día; comparte
    el límite semanal con `event_impact` y `market_move`. Si la noticia ya avisó como estimada y
    ahora está medida, rehace ese aviso en lugar de crear otro. Devuelve cuántos avisos ha creado
    o rehecho.

    Sin `force`, se comprueba al leer los avisos, como mucho cada `NEWS_CHECK_EVERY`, y no en
    modo demo (`NEWS_ESTIMATE_IN_DEMO`). `force=True` lo lanza ya (`make news-alerts`)."""
    now = clock.now()
    if not force:
        if get_settings().demo_mode and not config.NEWS_ESTIMATE_IN_DEMO:
            return 0
        with _lock:
            last = _last_news_check.get(portfolio_id)
            if last is not None and last <= now < last + config.NEWS_CHECK_EVERY:
                return 0
            _last_news_check[portfolio_id] = now
    items = [
        item
        for item in news_service.list_for_portfolio(portfolio_id, affecting=True, limit=200)
        if item.published_at >= now - config.NEWS_LOOKBACK and item.estimate is not None
    ]
    if not items:
        return 0
    portfolio = portfolio_service.get_valued(portfolio_id)  # mismo total que `status`
    factor = news_estimate.profile_factor(portfolio.risk_profile, portfolio.profile.value)
    changed = 0
    candidates: list[tuple[Decimal, NewsItemOut]] = []
    for item in items:
        estimate = item.estimate
        assert estimate is not None and estimate.low_eur is not None
        assert estimate.high_eur is not None
        existing = repository.find_news(portfolio_id, item.id)
        if existing is not None:
            changed += _refresh_measured(existing, item, portfolio.total_eur, factor)
            continue
        score = news_estimate.score_if_alert(
            estimate.low_eur, estimate.high_eur, portfolio.total_eur, factor
        )
        if score is None:
            continue
        if estimate.event_id and repository.exists(
            portfolio_id, estimate.event_id, AlertKind.EVENT_IMPACT
        ):
            continue  # el evento medido ya avisó: no hay aviso doble
        candidates.append((score, item))
    if not candidates:
        return changed
    score, item = min(candidates, key=lambda c: (-c[0], c[1].id))  # la que más mueve
    message = agents_service.write_news_alert_message(item)
    with _lock:
        if not _news_allowed(portfolio_id, now):
            return changed
        assert item.estimate is not None
        repository.save(
            portfolio_id,
            None,
            AlertKind.NEWS_ESTIMATE,
            score.quantize(_SCORE_STEP, rounding=ROUND_HALF_EVEN),
            message,
            now,
            calc_id=item.estimate.calc_id,
            news_id=item.id,
        )
    return changed + 1


def _refresh_measured(
    existing: repository.StoredAlert, item: NewsItemOut, total_eur: Decimal, factor: Decimal
) -> int:
    """Estimado → medido: rehace el aviso con la cifra medida (no gasta cupo)."""
    estimate = item.estimate
    if estimate is None or estimate.status is not NewsEstimateStatus.MEASURED:
        return 0
    message = agents_service.write_news_alert_message(item)
    if message == existing.message and estimate.calc_id == existing.calc_id:
        return 0
    assert estimate.impact_eur is not None
    score = abs(estimate.impact_eur) / news_estimate.threshold_eur(total_eur, factor)
    repository.update(
        existing.id,
        score.quantize(_SCORE_STEP, rounding=ROUND_HALF_EVEN),
        message,
        estimate.calc_id,
    )
    return 1


def _news_allowed(portfolio_id: str, now: datetime) -> bool:
    """Sin aviso `news_estimate` nuevo hoy y con cupo en la semana ISO. Llamar con `_lock`."""
    today = market_move.day_bounds(now)
    if repository.exists_between(portfolio_id, AlertKind.NEWS_ESTIMATE, *today):
        return False
    week_start, week_end = engine.iso_week_bounds(now)
    return engine.within_weekly_limit(repository.count_between(portfolio_id, week_start, week_end))


def list_alerts(portfolio_id: str) -> list[AlertOut]:
    portfolio_service.ensure_exists(portfolio_id)  # NOT_FOUND si la cartera no existe
    check_market_move(portfolio_id)
    check_news(portfolio_id)
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
            calc_id=a.calc_id or (calc_ids.get(a.event_id) if a.event_id else None),
            news_id=a.news_id,
        )
        for a in repository.list_for(portfolio_id)
    ]
