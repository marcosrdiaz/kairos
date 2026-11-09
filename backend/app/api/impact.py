"""Endpoints de impacto: eventos por cartera, escenarios y atribución (diseño del MVP §4.3)."""

from typing import Any

from fastapi import APIRouter, Query

from app.impact import service
from app.schemas.common import ErrorOut
from app.schemas.impact import (
    EventImpactOut,
    MoveAttributionOut,
    MovePeriod,
    ScenarioOut,
    ScenarioRequest,
)

router = APIRouter(tags=["impact"])

_RESPONSES: dict[int | str, dict[str, Any]] = {404: {"model": ErrorOut}, 422: {"model": ErrorOut}}


@router.get(
    "/portfolios/{portfolio_id}/events", response_model=list[EventImpactOut], responses=_RESPONSES
)
def list_event_impacts(
    portfolio_id: str, days: int = Query(default=7, ge=1)
) -> list[EventImpactOut]:
    return service.list_event_impacts(portfolio_id, days)


@router.post(
    "/portfolios/{portfolio_id}/scenarios", response_model=ScenarioOut, responses=_RESPONSES
)
def estimate_scenario(portfolio_id: str, body: ScenarioRequest) -> ScenarioOut:
    return service.estimate_scenario(portfolio_id, body.factor_shocks)


@router.get(
    "/portfolios/{portfolio_id}/move", response_model=MoveAttributionOut, responses=_RESPONSES
)
def explain_move(portfolio_id: str, period: MovePeriod = "week") -> MoveAttributionOut:
    """«¿Por qué ha bajado?» (`explain_move`, T2-07)."""
    return service.explain_move(portfolio_id, period)
