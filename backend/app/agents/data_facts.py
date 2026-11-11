"""Cifras (`Fact`) y evidencias de las herramientas de datos del asistente (T4-14): estado,
noticias, avisos, radar y agenda. Como `facts.py`: solo copian valores ya calculados por otros
módulos y los formatean; no calculan nada. Funciones puras.

Los textos que ya pasaron por el guardián o salen de plantillas deterministas (mensaje de un
aviso, título y detalle del radar, frase del estado) aportan sus cifras como evidencias con el
`calc_id` de su objeto, para que el asistente pueda citarlas con traza.
"""

from collections.abc import Iterable
from decimal import Decimal

from app.agents import guardian
from app.agents.fact_format import fraction, money, number
from app.schemas.agents import Evidence, Fact
from app.schemas.alerts import AlertOut
from app.schemas.news import NewsEstimateStatus, NewsItemOut
from app.schemas.planning import AgendaItemOut
from app.schemas.radar import RadarOut
from app.schemas.status import StatusOut

_TOP_POSITIONS = 3
_YEAR = "year"


def _direction(value: Decimal) -> str:
    return "a favor" if value > 0 else "en contra" if value < 0 else "sin efecto"


def traced_text_evidence(texts: Iterable[str | None], calc_id: str | None) -> list[Evidence]:
    """Cifras de un texto ya validado, con el `calc_id` de lo que describe."""
    evidence: list[Evidence] = []
    for text in texts:
        if not text:
            continue
        for figure in guardian.extract_figures(guardian.normalize(text)):
            evidence.append(
                Evidence(value=figure.value, unit=figure.unit, calc_id=calc_id, source=None)
            )
    return evidence


def year_evidence(years: Iterable[int], source: str) -> list[Evidence]:
    """Años de las fechas de los datos, para poder decir «en diciembre de 2026»."""
    return [Evidence(value=Decimal(y), unit=_YEAR, calc_id=None, source=source) for y in set(years)]


def status_facts(status: StatusOut) -> list[Fact]:
    cid = status.calc_id
    out = [
        money("status.total", "patrimonio", status.total_eur, cid),
        fraction("status.change_week_pct", "variación semanal en %", status.change_week_pct, cid),
    ]
    impact = status.reason.event_impact_eur
    if impact is not None:
        label = f"impacto del evento que explica el estado ({_direction(impact)})"
        out.append(money("status.event_impact", label, impact, cid))
    return out


def news_facts(item: NewsItemOut) -> list[Fact]:
    """Impacto estimado o medido de una noticia en la cartera; nada si no lo hay."""
    estimate = item.estimate
    if estimate is None or estimate.status not in (
        NewsEstimateStatus.ESTIMATED,
        NewsEstimateStatus.MEASURED,
    ):
        return []
    cid = estimate.calc_id or ""
    kind = "medido" if estimate.status is NewsEstimateStatus.MEASURED else "estimado"
    prefix, title = f"news.{item.id}", item.title
    out: list[Fact] = []
    pairs = (
        ("impact", "impacto", estimate.impact_eur, estimate.impact_pct),
        ("low", "extremo bajo del rango", estimate.low_eur, estimate.low_pct),
        ("high", "extremo alto del rango", estimate.high_eur, estimate.high_pct),
    )
    for key, label, eur, pct in pairs:
        if eur is not None:
            text = f"{label} {kind} de «{title}» ({_direction(eur)})"
            out.append(money(f"{prefix}.{key}", text, eur, cid))
        if pct is not None:
            text = f"{label} {kind} de «{title}» sobre el patrimonio"
            out.append(fraction(f"{prefix}.{key}_pct", text, pct, cid))
    if estimate.horizon_sessions is not None:
        label = f"plazo en sesiones del rango de «{title}»"
        out.append(number(f"{prefix}.horizon", label, Decimal(estimate.horizon_sessions), cid))
    top = sorted(estimate.positions, key=lambda p: abs(p.impact_eur), reverse=True)
    for position in top[:_TOP_POSITIONS]:
        label = f"impacto {kind} de «{title}» en {position.name}"
        out.append(money(f"{prefix}.pos.{position.asset_id}", label, position.impact_eur, cid))
    return out


def news_text_evidence(item: NewsItemOut) -> list[Evidence]:
    """Cifras que trae la propia noticia (titular y resumen de la fuente) y su año: no son de
    ninguna cartera."""
    source = f"news:{item.id}"
    evidence: list[Evidence] = []
    for text in (item.title, item.summary):
        for figure in guardian.extract_figures(guardian.normalize(text)):
            evidence.append(
                Evidence(value=figure.value, unit=figure.unit, calc_id=None, source=source)
            )
    return evidence + year_evidence([item.published_at.year], source)


def alert_evidence(alerts: list[AlertOut]) -> list[Evidence]:
    evidence: list[Evidence] = []
    for alert in alerts:
        evidence += traced_text_evidence([alert.message], alert.calc_id)
    return evidence + year_evidence([a.created_at.year for a in alerts], "alerts")


def radar_facts(radar: RadarOut) -> list[Fact]:
    out: list[Fact] = []
    for item in radar.items:
        if item.value_eur is not None:
            out.append(money(f"radar.{item.id}.value", item.title, item.value_eur, item.calc_id))
        if item.weight is not None:
            out.append(fraction(f"radar.{item.id}.weight", item.title, item.weight, item.calc_id))
    return out


def radar_evidence(radar: RadarOut) -> list[Evidence]:
    evidence: list[Evidence] = []
    for item in radar.items:
        evidence += traced_text_evidence([item.title, item.detail], item.calc_id)
    return evidence


def agenda_facts(items: list[AgendaItemOut]) -> list[Fact]:
    out: list[Fact] = []
    for index, item in enumerate(items):
        if item.exposed_eur is not None:
            label = f"parte de la cartera expuesta a «{item.title}»"
            out.append(money(f"agenda.{index}.exposed", label, item.exposed_eur, item.calc_id))
        if item.exposed_weight is not None:
            label = f"peso de la cartera expuesto a «{item.title}»"
            out.append(fraction(f"agenda.{index}.weight", label, item.exposed_weight, item.calc_id))
    return out


def agenda_evidence(items: list[AgendaItemOut]) -> list[Evidence]:
    evidence: list[Evidence] = []
    for item in items:
        evidence += traced_text_evidence([item.title], item.calc_id)
    return evidence + year_evidence([item.date.year for item in items], "agenda")
