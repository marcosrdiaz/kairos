"""Reglas del estado del widget (`SPEC.md` §8.6): funciones puras, sin BD."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.schemas import examples
from app.schemas.agents import StatusState
from app.schemas.impact import EventImpactOut
from app.status import engine

NOW = datetime(2026, 11, 8, 18, 0, tzinfo=UTC)
TOTAL = Decimal("40000")  # el 0,5 % son 200 €, por encima de los 150 € del mínimo


def _impact(eur: str, *, hours_ago: int = 1, event_id: str = "evento") -> EventImpactOut:
    base = EventImpactOut.model_validate(examples.load("EventImpactOut"))
    return base.model_copy(
        update={
            "event_id": event_id,
            "impact_eur": Decimal(eur),
            "occurred_at": NOW - timedelta(hours=hours_ago),
        }
    )


def test_tranquilo_without_events_or_drift() -> None:
    assert engine.evaluate(TOTAL, [], drift_exceeded=False, now=NOW) == (
        StatusState.TRANQUILO,
        None,
    )


def test_atento_at_exactly_the_share_threshold() -> None:
    impact = _impact("-200.00")
    assert engine.evaluate(TOTAL, [impact], drift_exceeded=False, now=NOW) == (
        StatusState.ATENTO,
        impact,
    )


def test_not_atento_just_under_the_share_threshold() -> None:
    state, event = engine.evaluate(TOTAL, [_impact("199.99")], drift_exceeded=False, now=NOW)
    assert (state, event) == (StatusState.TRANQUILO, None)


def test_small_portfolio_uses_the_150_euro_minimum() -> None:
    small = Decimal("1000")
    assert engine.is_significant(Decimal("-150"), small)
    assert not engine.is_significant(Decimal("-149.99"), small)


def test_event_at_exactly_72_hours_counts() -> None:
    state, _ = engine.evaluate(
        TOTAL, [_impact("-500", hours_ago=72)], drift_exceeded=False, now=NOW
    )
    assert state is StatusState.ATENTO


def test_event_older_than_72_hours_does_not_count() -> None:
    """La fecha que manda es la del evento, no la del cálculo: la precarga del guion."""
    state, _ = engine.evaluate(
        TOTAL, [_impact("-500", hours_ago=96)], drift_exceeded=False, now=NOW
    )
    assert state is StatusState.TRANQUILO


def test_atento_takes_precedence_over_drift() -> None:
    state, _ = engine.evaluate(TOTAL, [_impact("-500")], drift_exceeded=True, now=NOW)
    assert state is StatusState.ATENTO


def test_revisa_plan_with_drift_and_no_significant_event() -> None:
    assert engine.evaluate(TOTAL, [_impact("-10")], drift_exceeded=True, now=NOW) == (
        StatusState.REVISA_PLAN,
        None,
    )


def test_the_most_recent_significant_event_is_the_reason() -> None:
    older = _impact("-900", hours_ago=30, event_id="antiguo")
    newer = _impact("300", hours_ago=2, event_id="reciente")
    ignored = _impact("-1", hours_ago=1, event_id="pequeno")
    _, event = engine.evaluate(TOTAL, [older, ignored, newer], drift_exceeded=False, now=NOW)
    assert event == newer
