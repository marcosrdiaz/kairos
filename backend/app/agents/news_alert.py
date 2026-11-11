"""Aviso por noticia (`kind=news_estimate`, T4-31): cifras (`Fact`) y plantilla. Funciones puras.

Solo copia las cifras de la estimación del motor de impacto (`NewsEstimateOut`, T4-30): ninguna
la pone el LLM (regla 1). El texto dice «se estima» o «ya medido», el rango y el plazo; describe,
no alarma ni da órdenes. Pasa por el guardián en `service.write_news_alert_message`.
"""

from decimal import Decimal

from app.agents.fact_format import format_eur, money, number
from app.schemas.agents import Fact
from app.schemas.news import NewsEstimateOut, NewsEstimateStatus, NewsItemOut


def _figures(item: NewsItemOut) -> NewsEstimateOut:
    estimate = item.estimate
    if estimate is None or estimate.status not in (
        NewsEstimateStatus.ESTIMATED,
        NewsEstimateStatus.MEASURED,
    ):
        raise ValueError("Solo avisa una noticia estimada o medida")
    return estimate


def _ends(estimate: NewsEstimateOut) -> tuple[Decimal, Decimal]:
    """Extremos del rango, del más cercano a cero al más lejano. En un estimado tienen el mismo
    signo (si el rango cruza el cero no hay aviso)."""
    assert estimate.low_eur is not None and estimate.high_eur is not None
    low, high = estimate.low_eur, estimate.high_eur
    return (low, high) if abs(low) <= abs(high) else (high, low)


def news_facts(item: NewsItemOut) -> list[Fact]:
    estimate = _figures(item)
    assert estimate.calc_id is not None and estimate.impact_eur is not None
    assert estimate.horizon_sessions is not None
    cid = estimate.calc_id
    near, far = _ends(estimate)
    return [
        money("news.impact", "efecto central en la cartera", estimate.impact_eur, cid),
        money("news.near", "extremo del rango más cercano a cero", near, cid),
        money("news.far", "extremo del rango más lejano de cero", far, cid),
        number("news.horizon", "plazo en sesiones", Decimal(estimate.horizon_sessions), cid),
    ]


def _horizon(sessions: int) -> str:
    return "en la próxima sesión" if sessions == 1 else f"en las próximas {sessions} sesiones"


def news_alert_message(item: NewsItemOut) -> str:
    estimate = _figures(item)
    assert estimate.impact_eur is not None and estimate.horizon_sessions is not None
    near, far = _ends(estimate)
    span = f"entre {format_eur(near)} y {format_eur(far)}"
    if estimate.status is NewsEstimateStatus.MEASURED:
        # Medido: recoge todo lo que movió el mercado ese día, no solo la noticia (D-103). El rango
        # medido puede cruzar el cero si el estimado ya había avisado.
        impact = estimate.impact_eur
        if impact == 0:
            return f"{item.title}: ya medido, el día de la noticia tu cartera apenas se movió."
        moved = "subió" if impact > 0 else "bajó"
        detail = f", {span}" if near * far > 0 else ""
        return (
            f"{item.title}: ya medido, el día de la noticia tu cartera {moved} unos "
            f"{format_eur(impact)}{detail}."
        )
    moves = "suba" if near > 0 else "baje"
    return (
        f"{item.title}: se estima que tu cartera {moves} {span} "
        f"{_horizon(estimate.horizon_sessions)}."
    )
