"""Mock del motor de impacto: sirve los ejemplos de `schemas/examples/` (D-018).

Sin BD ni cálculo. Lo sustituyen T1-13 y T2-07; se borra en T2-03.
"""

from app.portfolio import service as portfolio_service
from app.schemas import examples
from app.schemas.impact import EventImpactOut, MoveAttributionOut, MovePeriod, ScenarioOut

_EVENT_EXAMPLES = ("EventImpactOut", "EventImpactOut.nvda")


def _event(name: str, portfolio_id: str) -> EventImpactOut:
    event = EventImpactOut.model_validate(examples.load(name))
    return event.model_copy(update={"portfolio_id": portfolio_id})


def list_event_impacts(portfolio_id: str) -> list[EventImpactOut]:
    portfolio_service.ensure_exists(portfolio_id)  # 404 si no existe
    return [_event(name, portfolio_id) for name in _EVENT_EXAMPLES]


def compute_event_impact(portfolio_id: str) -> EventImpactOut:
    portfolio_service.ensure_exists(portfolio_id)  # 404 si no existe
    return _event(_EVENT_EXAMPLES[0], portfolio_id)


def estimate_scenario(portfolio_id: str) -> ScenarioOut:
    portfolio_service.ensure_exists(portfolio_id)  # 404 si no existe
    return ScenarioOut.model_validate(examples.load("ScenarioOut"))


def explain_move(portfolio_id: str, period: MovePeriod) -> MoveAttributionOut:
    portfolio_service.ensure_exists(portfolio_id)  # 404 si no existe
    move = MoveAttributionOut.model_validate(examples.load("MoveAttributionOut"))
    return move.model_copy(update={"period": period})
