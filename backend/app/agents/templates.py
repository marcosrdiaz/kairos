"""Plantillas deterministas del explicador y de los textos de widget, avisos y eventos (D-010).

Se usan cuando el modelo no está (sin clave o caído) o cuando una frase se bloquea dos veces.
Solo copian cifras ya calculadas, formateadas igual que los `facts`, y también pasan por el
guardián antes de llegar al usuario. Tampoco dan órdenes: describen.
"""

import re
from decimal import Decimal
from enum import StrEnum

from app.agents import guardian
from app.agents.context import Preloaded
from app.agents.fact_format import format_eur, format_fraction
from app.schemas.agents import EventImpactStub, QuestionKind, StatusFacts, StatusState
from app.schemas.impact import EventImpactOut, MoveAttributionOut


class Topic(StrEnum):
    MOVE = "move"
    EVENT = "event"
    PLAN = "plan"
    GENERAL = "general"


_TOPICS: tuple[tuple[Topic, re.Pattern[str]], ...] = (
    (Topic.PLAN, re.compile(r"voy bien|mi plan|\bplan\b|objetivo|\bmeta\b|jubilaci|llegare|aport")),
    (
        Topic.EVENT,
        re.compile(
            r"\bbce\b|banco central|\btipos\b|petroleo|brent|nvidia|resultados|noticia|evento"
            r"|dolar|\bfed\b|inflacion|\blo de(?:l)?\b|\bafecta"
        ),
    ),
    (Topic.MOVE, re.compile(r"bajad|subid|caid|por que|perdid|ganad|semana|\bhoy\b|movid|\bmes\b")),
)
_EVENT_HINTS: dict[str, tuple[str, ...]] = {
    "bce": ("bce", "central", "tipos"),
    "tipos": ("bce", "central", "tipos"),
    "petroleo": ("oil", "petroleo", "brent", "crudo"),
    "brent": ("oil", "petroleo", "brent", "crudo"),
    "nvidia": ("nvda", "nvidia", "tecnolog", "resultados"),
    "tecnolog": ("nvda", "nvidia", "tecnolog", "resultados"),
    "resultados": ("nvda", "nvidia", "tecnolog", "resultados"),
    "dolar": ("usd", "dolar", "divisa"),
}
_PERIOD_START = {"day": "Hoy", "week": "Esta semana", "month": "Este mes"}


def topic(question: str) -> Topic:
    normalized = guardian.normalize(question)
    for name, pattern in _TOPICS:
        if pattern.search(normalized):
            return name
    return Topic.GENERAL


def question_kind(question_topic: Topic) -> QuestionKind:
    """Impacto (la primera frase lleva una cifra en €) para movimientos y eventos."""
    impact = question_topic in {Topic.MOVE, Topic.EVENT}
    return QuestionKind.IMPACT if impact else QuestionKind.GENERAL


def _side(value: Decimal) -> str:
    return "a tu favor" if value >= 0 else "en contra"


def _more_less(value: Decimal) -> str:
    return "más" if value >= 0 else "menos"


def _amount(value: Decimal) -> str:
    """Importe con su sentido; 0 es «0 euros», sin «a tu favor»."""
    return format_eur(value) if value == 0 else f"{format_eur(value)} {_side(value)}"


def _change(value: Decimal) -> str:
    if value == 0:
        return "se ha quedado igual"
    return f"ha {'subido' if value > 0 else 'bajado'} {format_eur(value)}"


def match_event(events: list[EventImpactOut], question: str) -> EventImpactOut | None:
    """El evento al que se refiere la pregunta o, si no se sabe, el de mayor impacto."""
    if not events:
        return None
    normalized = guardian.normalize(question)
    hints = {hint for key, values in _EVENT_HINTS.items() if key in normalized for hint in values}

    def score(event: EventImpactOut) -> tuple[int, Decimal]:
        haystack = guardian.normalize(f"{event.event_id} {event.title}")
        return sum(1 for hint in hints if hint in haystack), abs(event.impact_eur)

    return max(events, key=score)


def _event_sentences(event: EventImpactOut) -> list[str]:
    impact = event.impact_eur
    span = f"en un rango que va de {_amount(event.low_eur)} a {_amount(event.high_eur)}"
    if impact == 0:
        first = f"«{event.title}» no mueve tu cartera en la estimación central, {span}."
    else:
        first = f"«{event.title}» te afecta en unos {_amount(impact)}, {span}."
    sentences = [first]
    if event.breakdown:
        top = max(event.breakdown, key=lambda a: abs(a.impact_eur))
        sentences.append(f"Donde más se nota es en {top.name}, por el canal de {top.channel}.")
    sentences.append(f"La confianza de esta estimación es {event.confidence.value}.")
    return sentences


def _total(pre: Preloaded) -> str:
    total = pre.fact("total")
    return f"Tu cartera vale {total.display}" if total else "Tu cartera está al día"


def _general(pre: Preloaded) -> list[str]:
    week = pre.fact("change_week")
    sentences = [f"{_total(pre)}."]
    if week is not None:
        sentences.append(f"Esta semana {_change(week.value)}.")
    return sentences


def _move(pre: Preloaded, move: MoveAttributionOut | None) -> list[str]:
    if move is None:
        week = pre.fact("change_week")
        if week is None:
            return _general(pre)
        sentences = [f"Esta semana tu cartera {_change(week.value)}."]
        if pre.events:
            event = max(pre.events, key=lambda e: abs(e.impact_eur))
            sentences.append(
                f"El evento que más pesa es «{event.title}», con unos {_amount(event.impact_eur)}."
            )
        return sentences
    start = _PERIOD_START.get(move.period, "En este periodo")
    sentences = [f"{start} tu cartera {_change(move.change_eur)}."]
    if move.by_event:
        top = max(move.by_event, key=lambda e: abs(e.impact_eur))
        sentences.append(
            f"La mayor parte viene de «{top.title}», con unos {_amount(top.impact_eur)}."
        )
    elif move.by_asset and any(a.change_eur != 0 for a in move.by_asset):
        asset = max(move.by_asset, key=lambda a: abs(a.change_eur))
        sentences.append(
            f"Lo que más ha pesado es {asset.name}, con {format_eur(asset.change_eur)} "
            f"{_more_less(asset.change_eur)}."
        )
    return sentences


def _event(pre: Preloaded, question: str) -> list[str]:
    event = match_event(pre.events, question)
    if event is None:
        return [f"{_total(pre)} y en los últimos 7 días no hay eventos con impacto en ella."]
    return _event_sentences(event)


def _plan(pre: Preloaded) -> list[str]:
    projection = pre.projection
    if projection is None:
        return _general(pre)
    goal, year = format_eur(projection.goal_amount_eur), projection.goal_year
    if projection.on_track:
        first = f"Según tu plan, en el escenario base llegas a tu objetivo de {goal} en {year}."
    else:
        first = (
            f"Con tu plan actual, en el escenario base te faltarían unos "
            f"{format_eur(projection.gap_eur)} para tu objetivo de {goal} en {year}."
        )
    sentences = [first]
    monthly = projection.monthly_contribution_eur
    sentences.append(f"La proyección cuenta con tus aportaciones de {format_eur(monthly)} al mes.")
    current, target = pre.fact("plan.equity_current"), pre.fact("plan.equity_target")
    if pre.context.plan.drift_exceeded and current and target:
        sentences.append(
            f"Tu renta variable está en {current.display}, lejos del {target.display} de tu plan."
        )
    return sentences


def answer(pre: Preloaded, question: str, move: MoveAttributionOut | None = None) -> list[str]:
    """Respuesta de plantilla a una pregunta. La primera frase lleva la cifra en € si toca."""
    question_topic = topic(question)
    if question_topic is Topic.MOVE:
        return _move(pre, move)
    if question_topic is Topic.EVENT:
        return _event(pre, question)
    if question_topic is Topic.PLAN:
        return _plan(pre)
    return _general(pre)


# --- Textos de widget, avisos y explicación de evento ---


def event_explanation(impact: EventImpactStub) -> str:
    value = impact.impact_eur
    span = f"en un rango que va de {_amount(impact.low_eur)} a {_amount(impact.high_eur)}"
    if value == 0:
        text = f"Este evento no mueve tu cartera en la estimación central, {span}."
    else:
        text = f"Este evento te afecta en unos {_amount(value)}, {span}."
    if impact.breakdown:
        top = max(impact.breakdown, key=lambda a: abs(a.impact_eur))
        text += f" Donde más se nota es en {top.name}, por el canal de {top.channel}."
    return text


def alert_message(impact: EventImpactStub) -> str:
    value = impact.impact_eur
    if value == 0:
        return f"{impact.title}: {format_eur(value)} de efecto en tu cartera."
    return f"{impact.title}: tu cartera, unos {format_eur(value)} {_more_less(value)}."


def status_sentence(facts: StatusFacts) -> str:
    if facts.state is StatusState.ATENTO:
        if facts.event_title and facts.event_impact_eur is not None:
            value = facts.event_impact_eur
            return (
                f"{facts.event_title}: unos {format_eur(value)} {_more_less(value)} en tu "
                "cartera. Toca para ver por qué."
            )
        return "Hay movimiento en tu cartera. Toca para ver por qué."
    if facts.state is StatusState.REVISA_PLAN:
        if facts.equity_current is not None and facts.equity_target is not None:
            side = "por encima" if facts.equity_current > facts.equity_target else "por debajo"
            return (
                f"Tu renta variable está en {format_fraction(facts.equity_current)}, {side} del "
                f"{format_fraction(facts.equity_target)} de tu plan. Toca para ver el detalle."
            )
        return "Tu cartera se ha alejado de tu plan. Toca para ver el detalle."
    return f"Todo en calma: tu cartera vale {format_eur(facts.total_eur)}."


SAFE_TEXT = "Hay novedades en tu cartera. Abre KAIROS para ver el detalle."
"""Último recurso si hasta la plantilla se bloquea: sin cifras y sin órdenes."""
