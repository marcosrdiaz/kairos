"""Herramientas del explicador (`agents/tools.py`): cada una llama al servicio de su módulo y
devuelve el contrato más `facts` con `display` y `calc_id`."""

import json
from decimal import Decimal
from typing import Any

import pytest

from app.agents import tools
from app.core.errors import AppError, ErrorCode
from app.exposure import service as exposure_service
from app.impact import service as impact_service
from app.planning import service as planning_service
from app.portfolio import service as portfolio_service
from app.schemas import examples
from app.schemas.common import Factor
from app.schemas.exposure import ExposureOut
from app.schemas.impact import ScenarioOut
from tests.fakes import explainer as fx


class _Recorder:
    def __init__(self, result: Any) -> None:
        self.result = result
        self.calls: list[tuple[Any, ...]] = []

    def __call__(self, *args: Any) -> Any:
        self.calls.append(args)
        return self.result


def _payload(result: tools.ToolResult) -> dict[str, Any]:
    assert not result.is_error, result.content
    data: dict[str, Any] = json.loads(result.content)
    assert data["facts"], "la herramienta debe devolver facts"
    assert all(f["calc_id"] and f["display"] for f in data["facts"])
    return data


def test_get_portfolio(monkeypatch: pytest.MonkeyPatch) -> None:
    rec = _Recorder(fx.portfolio())
    monkeypatch.setattr(portfolio_service, "get_valued", rec)
    data = _payload(tools.run("laura", "get_portfolio", {}))
    assert rec.calls == [("laura",)]
    assert data["result"]["calc_id"] == fx.portfolio().calc_id
    assert {"total", "change_week"} <= {f["key"] for f in data["facts"]}


def test_get_exposure(monkeypatch: pytest.MonkeyPatch) -> None:
    rec = _Recorder(ExposureOut.model_validate(examples.load("ExposureOut")))
    monkeypatch.setattr(exposure_service, "get_exposure", rec)
    data = _payload(tools.run("laura", "get_exposure", {}))
    assert rec.calls == [("laura",)]
    country = next(f for f in data["facts"] if f["key"] == "exposure.top_country")
    assert country["display"] == "61 %"


def test_get_events(monkeypatch: pytest.MonkeyPatch) -> None:
    rec = _Recorder(fx.events())
    monkeypatch.setattr(impact_service, "list_event_impacts", rec)
    data = _payload(tools.run("laura", "get_events", {"days": 3}))
    assert rec.calls == [("laura", 3)]
    keys = {f["key"] for f in data["facts"]}
    assert {"evt.bce-2025-06.impact", "evt.nvda-2025-02.low"} <= keys


def test_estimate_impact_parses_shocks_as_decimal(monkeypatch: pytest.MonkeyPatch) -> None:
    scenario = ScenarioOut.model_validate(examples.load("ScenarioOut"))
    rec = _Recorder(scenario)
    monkeypatch.setattr(impact_service, "estimate_scenario", rec)
    args = {"factor_shocks": [{"factor": "OIL", "shock": "0.10"}]}
    data = _payload(tools.run("laura", "estimate_impact", args))
    assert rec.calls == [("laura", {Factor.OIL: Decimal("0.10")})]
    assert any(f["key"] == "scenario.impact" for f in data["facts"])


def test_check_plan_calls_portfolio_and_planning(monkeypatch: pytest.MonkeyPatch) -> None:
    plan, projection = _Recorder(fx.plan()), _Recorder(fx.projection())
    monkeypatch.setattr(portfolio_service, "get_plan", plan)
    monkeypatch.setattr(planning_service, "get_projection", projection)
    data = _payload(tools.run("laura", "check_plan", {}))
    assert plan.calls == projection.calls == [("laura",)]
    assert set(data["result"]) == {"plan", "projection"}
    year = next(f for f in data["facts"] if f["key"] == "projection.goal_year")
    assert (year["unit"], year["display"]) == ("year", "2040")


def test_explain_move(monkeypatch: pytest.MonkeyPatch) -> None:
    rec = _Recorder(fx.move())
    monkeypatch.setattr(impact_service, "explain_move", rec)
    data = _payload(tools.run("laura", "explain_move", {"period": "week"}))
    assert rec.calls == [("laura", "week")]
    change = next(f for f in data["facts"] if f["key"] == "move.change")
    assert change["display"] == "514 euros"


@pytest.mark.parametrize(
    ("name", "args"),
    [
        ("get_events", {"days": 0}),
        ("get_events", {"days": "siete"}),
        ("explain_move", {"period": "year"}),
        ("estimate_impact", {"factor_shocks": []}),
        ("estimate_impact", {"factor_shocks": [{"factor": "GOLD", "shock": "0.1"}]}),
        ("estimate_impact", {"factor_shocks": [{"factor": "OIL", "shock": "5"}]}),
        ("estimate_impact", {"factor_shocks": [{"factor": "OIL", "shock": "mucho"}]}),
        ("no_existe", {}),
    ],
)
def test_invalid_input_is_a_controlled_error(name: str, args: dict[str, Any]) -> None:
    result = tools.run("laura", name, args)
    assert result.is_error
    assert result.facts == []


def test_module_errors_become_tool_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*_: Any) -> Any:
        raise AppError(ErrorCode.PRICE_UNAVAILABLE, "Sin precio.")

    monkeypatch.setattr(portfolio_service, "get_valued", fail)
    result = tools.run("laura", "get_portfolio", {})
    assert result.is_error
    assert "PRICE_UNAVAILABLE" in result.content


@pytest.mark.parametrize("error", [KeyError("x"), TypeError("y"), RuntimeError("z")])
def test_unexpected_errors_become_a_fixed_tool_error(
    monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    def fail(*_: Any) -> Any:
        raise error

    monkeypatch.setattr(exposure_service, "get_exposure", fail)
    result = tools.run("laura", "get_exposure", {})
    assert result == tools.ToolResult(tools.TOOL_FAILED, is_error=True)
    assert not any(ch.isdigit() for ch in tools.TOOL_FAILED)


def test_definitions_match_handlers() -> None:
    names = [d["name"] for d in tools.DEFINITIONS]
    assert names == ["list_portfolios", *tools._HANDLERS]
    for definition in tools.DEFINITIONS:
        assert definition["input_schema"]["additionalProperties"] is False
        if definition["name"] != "list_portfolios":
            assert "portfolio_id" in definition["input_schema"]["properties"]
            assert "portfolio_id" not in definition["input_schema"]["required"]
