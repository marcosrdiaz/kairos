"""Herramientas del explicador (diseño del MVP §4.4, `SPEC.md` §9).

Cada herramienta llama al `service.py` del módulo dueño y devuelve su contrato más una lista
`facts` con la misma forma que el contexto precargado. Las cifras de esos `facts` pasan a ser
evidencias del guardián durante el resto del turno. Un error del módulo vuelve como resultado de
error (`is_error`) para que el modelo lo diga sin inventar nada.
"""

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, get_args

from pydantic import BaseModel

from app.agents import facts
from app.core.errors import AppError
from app.exposure import service as exposure_service
from app.impact import service as impact_service
from app.planning import service as planning_service
from app.portfolio import service as portfolio_service
from app.schemas.agents import Fact
from app.schemas.common import Factor
from app.schemas.impact import MovePeriod

MAX_DAYS = 30
MAX_SHOCK = Decimal(1)
_PERIODS: tuple[str, ...] = get_args(MovePeriod)


class ToolInputError(ValueError):
    """La entrada que ha dado el modelo no es válida."""


@dataclass(frozen=True)
class ToolResult:
    content: str
    facts: list[Fact] = field(default_factory=list)
    is_error: bool = False


def _dump(*models: BaseModel | list[Any]) -> list[Any]:
    out: list[Any] = []
    for model in models:
        if isinstance(model, list):
            out.append([item.model_dump(mode="json") for item in model])
        else:
            out.append(model.model_dump(mode="json"))
    return out


def _ok(result: Any, found: list[Fact]) -> ToolResult:
    payload = {"result": result, "facts": [f.model_dump(mode="json") for f in found]}
    return ToolResult(json.dumps(payload, ensure_ascii=False), found)


def get_portfolio(portfolio_id: str, _: Mapping[str, Any]) -> ToolResult:
    portfolio = portfolio_service.get_valued(portfolio_id)
    return _ok(_dump(portfolio)[0], facts.portfolio_facts(portfolio))


def get_exposure(portfolio_id: str, _: Mapping[str, Any]) -> ToolResult:
    exposure = exposure_service.get_exposure(portfolio_id)
    return _ok(_dump(exposure)[0], facts.exposure_facts(exposure))


def get_events(portfolio_id: str, args: Mapping[str, Any]) -> ToolResult:
    days = args.get("days", 7)
    if not isinstance(days, int) or isinstance(days, bool) or not 1 <= days <= MAX_DAYS:
        raise ToolInputError(f"`days` debe ser un entero entre 1 y {MAX_DAYS}")
    events = impact_service.list_event_impacts(portfolio_id, days)
    found = [fact for event in events for fact in facts.event_impact_facts(event)]
    return _ok(_dump(events)[0], found)


def _shocks(raw: Any) -> dict[Factor, Decimal]:
    if not isinstance(raw, list) or not raw:
        raise ToolInputError("`factor_shocks` debe ser una lista no vacía")
    shocks: dict[Factor, Decimal] = {}
    for item in raw:
        if not isinstance(item, Mapping):
            raise ToolInputError("cada movimiento lleva `factor` y `shock`")
        try:
            factor = Factor(str(item.get("factor")))
            shock = Decimal(str(item.get("shock")))
        except (ValueError, InvalidOperation) as error:
            raise ToolInputError(f"movimiento no válido: {item}") from error
        if not shock.is_finite() or abs(shock) > MAX_SHOCK:
            raise ToolInputError("`shock` es una fracción entre -1 y 1 (−0.10 = −10 %)")
        shocks[factor] = shock
    return shocks


def estimate_impact(portfolio_id: str, args: Mapping[str, Any]) -> ToolResult:
    scenario = impact_service.estimate_scenario(portfolio_id, _shocks(args.get("factor_shocks")))
    return _ok(_dump(scenario)[0], facts.scenario_facts(scenario))


def check_plan(portfolio_id: str, _: Mapping[str, Any]) -> ToolResult:
    plan = portfolio_service.get_plan(portfolio_id)
    projection = planning_service.get_projection(portfolio_id)
    plan_json, projection_json = _dump(plan, projection)
    found = [*facts.plan_facts(plan), *facts.projection_facts(projection)]
    return _ok({"plan": plan_json, "projection": projection_json}, found)


def explain_move(portfolio_id: str, args: Mapping[str, Any]) -> ToolResult:
    period = args.get("period", "week")
    if period not in _PERIODS:
        raise ToolInputError(f"`period` debe ser uno de {', '.join(_PERIODS)}")
    move = impact_service.explain_move(portfolio_id, period)
    return _ok(_dump(move)[0], facts.move_facts(move))


_HANDLERS: dict[str, Callable[[str, Mapping[str, Any]], ToolResult]] = {
    "get_portfolio": get_portfolio,
    "get_exposure": get_exposure,
    "get_events": get_events,
    "estimate_impact": estimate_impact,
    "check_plan": check_plan,
    "explain_move": explain_move,
}


def run(portfolio_id: str, name: str, args: Any) -> ToolResult:
    """Ejecuta una herramienta para la cartera del turno. Nunca lanza: los fallos vuelven como
    resultado de error. La cartera la fija el turno, no el modelo."""
    handler = _HANDLERS.get(name)
    if handler is None:
        return ToolResult(f"La herramienta «{name}» no existe.", is_error=True)
    try:
        return handler(portfolio_id, args if isinstance(args, Mapping) else {})
    except ToolInputError as error:
        return ToolResult(f"Entrada no válida: {error}", is_error=True)
    except AppError as error:
        return ToolResult(f"{error.code.value}: {error.message}", is_error=True)


def _schema(properties: dict[str, Any] | None = None, required: list[str] | None = None) -> Any:
    return {
        "type": "object",
        "properties": properties or {},
        "required": required or [],
        "additionalProperties": False,
    }


_FACTORS = [factor.value for factor in Factor]

DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "get_portfolio",
        "description": "Cartera valorada: patrimonio, variación semanal, asignación y posiciones.",
        "input_schema": _schema(),
    },
    {
        "name": "get_exposure",
        "description": "Exposición real por país, sector, divisa y empresa (look-through de los "
        "fondos), solapamientos y radiografía.",
        "input_schema": _schema(),
    },
    {
        "name": "get_events",
        "description": "Eventos de los últimos `days` días con su impacto estimado en la cartera, "
        "rango, confianza y desglose por activo.",
        "input_schema": _schema(
            {"days": {"type": "integer", "minimum": 1, "maximum": MAX_DAYS}}, ["days"]
        ),
    },
    {
        "name": "estimate_impact",
        "description": "Impacto estimado de un escenario hipotético que plantea el usuario («¿y "
        "si el petróleo sube…?»). Cada `shock` es la fracción que dice el usuario (−0.10 = −10 "
        "%). Usa solo movimientos que el usuario haya dicho: no los inventes.",
        "input_schema": _schema(
            {
                "factor_shocks": {
                    "type": "array",
                    "items": _schema(
                        {
                            "factor": {"type": "string", "enum": _FACTORS},
                            "shock": {"type": "string"},
                        },
                        ["factor", "shock"],
                    ),
                }
            },
            ["factor_shocks"],
        ),
    },
    {
        "name": "check_plan",
        "description": "Plan del usuario (asignación objetivo, desviación, meta) y proyección "
        "con sus aportaciones periódicas (DCA) frente a la meta.",
        "input_schema": _schema(),
    },
    {
        "name": "explain_move",
        "description": "Atribución del cambio de valor del periodo a activos y eventos.",
        "input_schema": _schema({"period": {"type": "string", "enum": list(_PERIODS)}}, ["period"]),
    },
]
