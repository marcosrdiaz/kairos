"""Herramientas del explicador (diseño del MVP §4.4, `SPEC.md` §9, T4-14).

Cada herramienta llama al `service.py` del módulo dueño y devuelve su contrato más una lista
`facts` con la misma forma que el contexto precargado. Las cifras de esos `facts` pasan a ser
evidencias del guardián durante el resto del turno, **de la cartera consultada** (`portfolio_id`
del resultado): una frase solo puede citarlas si habla de esa cartera (`portfolio_scope.py`).
Un error del módulo vuelve como resultado de error (`is_error`) para que el modelo lo diga sin
inventar nada.

El asistente puede consultar cualquier cartera del usuario con `portfolio_id`; sin él, la de la
pregunta o la elegida en la app (`default_portfolio`). Las definiciones están en `tool_defs.py`.
"""

import json
import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import BaseModel

from app.agents import data_facts, facts
from app.agents.fact_format import as_evidence
from app.agents.tool_defs import DEFINITIONS, MAX_DAYS, MAX_NEWS, PERIODS
from app.core.errors import AppError
from app.exposure import service as exposure_service
from app.impact import service as impact_service
from app.planning import service as planning_service
from app.portfolio import service as portfolio_service
from app.schemas.agents import Evidence, Fact
from app.schemas.common import Factor
from app.schemas.news import NewsCategory, NewsItemOut

__all__ = ["DEFINITIONS", "MAX_DAYS", "ToolInputError", "ToolResult", "run"]

MAX_SHOCK = Decimal(1)
DEFAULT_NEWS = 8
MAX_ALERTS = 10
_SUMMARY_CHARS = 300
TOOL_FAILED = "La herramienta ha fallado y no ha devuelto datos. No des cifras de esta parte."

logger = logging.getLogger(__name__)


class ToolInputError(ValueError):
    """La entrada que ha dado el modelo no es válida."""


@dataclass(frozen=True)
class ToolResult:
    content: str
    facts: list[Fact] = field(default_factory=list)
    is_error: bool = False
    portfolio_id: str | None = None
    """Cartera de la que son los `facts`; `None` si no son de ninguna."""
    shared: list[Evidence] = field(default_factory=list)
    """Cifras que no son de ninguna cartera (las del texto de una noticia)."""
    extra: list[Evidence] = field(default_factory=list)
    """Evidencias de la cartera que no son `facts` (cifras de textos ya validados)."""

    def evidence(self) -> list[Evidence]:
        """Evidencias de la cartera consultada."""
        return [*as_evidence(self.facts), *self.extra]


@dataclass(frozen=True)
class _Out:
    result: Any
    facts: list[Fact] = field(default_factory=list)
    shared: list[Evidence] = field(default_factory=list)
    extra: list[Evidence] = field(default_factory=list)
    """Evidencias de la cartera que no son `facts` (cifras de textos ya validados)."""


def _dump(model: BaseModel | list[Any]) -> Any:
    if isinstance(model, list):
        return [item.model_dump(mode="json") for item in model]
    return model.model_dump(mode="json")


# --- Herramientas por cartera: (portfolio_id, args) → _Out ---


def get_portfolio(portfolio_id: str, _: Mapping[str, Any]) -> _Out:
    portfolio = portfolio_service.get_valued(portfolio_id)
    return _Out(_dump(portfolio), facts.portfolio_facts(portfolio))


def get_status(portfolio_id: str, _: Mapping[str, Any]) -> _Out:
    from app.status import service as status_service  # status importa agents.service

    status = status_service.get_status(portfolio_id)
    extra = data_facts.traced_text_evidence([status.sentence], status.calc_id)
    return _Out(_dump(status), data_facts.status_facts(status), extra=extra)


def get_exposure(portfolio_id: str, _: Mapping[str, Any]) -> _Out:
    exposure = exposure_service.get_exposure(portfolio_id)
    return _Out(_dump(exposure), facts.exposure_facts(exposure))


def get_events(portfolio_id: str, args: Mapping[str, Any]) -> _Out:
    days = _int(args, "days", 7, MAX_DAYS)
    events = impact_service.list_event_impacts(portfolio_id, days)
    found = [fact for event in events for fact in facts.event_impact_facts(event)]
    return _Out(_dump(events), found)


def _news_json(item: NewsItemOut) -> Any:
    data = item.model_dump(mode="json", exclude={"channels"})
    summary = data.get("summary") or ""
    if len(summary) > _SUMMARY_CHARS:
        data["summary"] = summary[:_SUMMARY_CHARS].rstrip() + "…"
    return data


def _news_out(items: list[NewsItemOut]) -> _Out:
    found = [fact for item in items for fact in data_facts.news_facts(item)]
    shared = [ev for item in items for ev in data_facts.news_text_evidence(item)]
    return _Out([_news_json(item) for item in items], found, shared)


def get_news(portfolio_id: str, args: Mapping[str, Any]) -> _Out:
    from app.news import service as news_service  # news importa agents (clasificador)

    raw = args.get("category")
    try:
        category = NewsCategory(raw) if raw is not None else None
    except ValueError as error:
        raise ToolInputError(f"`category` no válida: {raw}") from error
    affecting = args.get("affecting", True)
    if not isinstance(affecting, bool):
        raise ToolInputError("`affecting` es true o false")
    limit = _int(args, "limit", DEFAULT_NEWS, MAX_NEWS)
    items = news_service.list_for_portfolio(portfolio_id, category, affecting, limit)
    return _news_out(items)


def get_news_item(portfolio_id: str, args: Mapping[str, Any]) -> _Out:
    from app.news import service as news_service

    news_id = args.get("news_id")
    if not isinstance(news_id, str) or not news_id:
        raise ToolInputError("falta `news_id`")
    return _news_out([news_service.get_for_portfolio(portfolio_id, news_id)])


def get_alerts(portfolio_id: str, _: Mapping[str, Any]) -> _Out:
    from app.alerts import service as alerts_service  # alerts importa agents.service

    alerts = sorted(
        alerts_service.list_alerts(portfolio_id), key=lambda a: a.created_at, reverse=True
    )[:MAX_ALERTS]
    return _Out(_dump(alerts), extra=data_facts.alert_evidence(alerts))


def get_radar(portfolio_id: str, _: Mapping[str, Any]) -> _Out:
    radar = exposure_service.get_radar(portfolio_id)
    extra = data_facts.radar_evidence(radar)
    return _Out(_dump(radar), data_facts.radar_facts(radar), extra=extra)


def get_agenda(portfolio_id: str, _: Mapping[str, Any]) -> _Out:
    items = planning_service.get_agenda(portfolio_id)
    extra = data_facts.agenda_evidence(items)
    return _Out(_dump(items), data_facts.agenda_facts(items), extra=extra)


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


def estimate_impact(portfolio_id: str, args: Mapping[str, Any]) -> _Out:
    scenario = impact_service.estimate_scenario(portfolio_id, _shocks(args.get("factor_shocks")))
    return _Out(_dump(scenario), facts.scenario_facts(scenario))


def check_plan(portfolio_id: str, _: Mapping[str, Any]) -> _Out:
    plan = portfolio_service.get_plan(portfolio_id)
    projection = planning_service.get_projection(portfolio_id)
    found = [*facts.plan_facts(plan), *facts.projection_facts(projection)]
    return _Out({"plan": _dump(plan), "projection": _dump(projection)}, found)


def explain_move(portfolio_id: str, args: Mapping[str, Any]) -> _Out:
    period = args.get("period", "week")
    if period not in PERIODS:
        raise ToolInputError(f"`period` debe ser uno de {', '.join(PERIODS)}")
    move = impact_service.explain_move(portfolio_id, period)
    return _Out(_dump(move), facts.move_facts(move))


def _int(args: Mapping[str, Any], key: str, default: int, maximum: int) -> int:
    value = args.get(key, default)
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= maximum:
        raise ToolInputError(f"`{key}` debe ser un entero entre 1 y {maximum}")
    return value


_HANDLERS: dict[str, Callable[[str, Mapping[str, Any]], _Out]] = {
    "get_portfolio": get_portfolio,
    "get_status": get_status,
    "get_exposure": get_exposure,
    "get_events": get_events,
    "get_news": get_news,
    "get_news_item": get_news_item,
    "get_alerts": get_alerts,
    "get_radar": get_radar,
    "get_agenda": get_agenda,
    "estimate_impact": estimate_impact,
    "check_plan": check_plan,
    "explain_move": explain_move,
}


# --- Ejecución ---


def _portfolio_list(default_portfolio: str | None) -> ToolResult:
    rows = [
        {
            "portfolio_id": item.id,
            "nombre": item.name,
            "tipo": item.kind.value if item.kind is not None else None,
            "perfil": item.risk_profile.value if item.risk_profile is not None else None,
            "elegida_en_la_app": item.id == default_portfolio,
        }
        for item in portfolio_service.list_portfolios()
    ]
    return ToolResult(json.dumps({"result": rows, "facts": []}, ensure_ascii=False))


def _resolve(
    default_portfolio: str | None, args: Mapping[str, Any], names: Mapping[str, str] | None
) -> tuple[str, str]:
    """Cartera de la llamada y su nombre. Lanza `ToolInputError` si no hay o no existe. Sin
    `names` no comprueba que exista: lo hace el servicio del módulo (404)."""
    raw = args.get("portfolio_id", default_portfolio)
    if names is None and isinstance(raw, str) and raw:
        return raw, raw
    known_names = names or {}
    if not isinstance(raw, str) or raw not in known_names:
        known = ", ".join(f"{pid} ({name})" for pid, name in known_names.items()) or "ninguna"
        what = "falta `portfolio_id`" if raw is None else f"no existe la cartera {raw!r}"
        raise ToolInputError(f"{what}; las carteras son: {known}")
    return raw, known_names[raw]


def run(
    default_portfolio: str | None,
    name: str,
    args: Any,
    portfolios: Mapping[str, str] | None = None,
) -> ToolResult:
    """Ejecuta una herramienta. Nunca lanza: los fallos vuelven como resultado de error.

    `portfolios` (id → nombre) son las carteras del usuario que puede consultar el turno."""
    mapping: Mapping[str, Any] = args if isinstance(args, Mapping) else {}
    if name == "list_portfolios":
        return _portfolio_list(default_portfolio)
    handler = _HANDLERS.get(name)
    if handler is None:
        return ToolResult(f"La herramienta «{name}» no existe.", is_error=True)
    portfolio_id: str | None = None
    try:
        portfolio_id, portfolio_name = _resolve(default_portfolio, mapping, portfolios)
        out = handler(portfolio_id, mapping)
    except ToolInputError as error:
        return ToolResult(f"Entrada no válida: {error}", is_error=True)
    except AppError as error:
        return ToolResult(f"{error.code.value}: {error.message}", is_error=True)
    except Exception:
        logger.exception("Herramienta %s: error inesperado (cartera %s)", name, portfolio_id)
        return ToolResult(TOOL_FAILED, is_error=True)
    payload = {
        "cartera": {"portfolio_id": portfolio_id, "nombre": portfolio_name},
        "result": out.result,
        "facts": [f.model_dump(mode="json") for f in out.facts],
    }
    content = json.dumps(payload, ensure_ascii=False)
    return ToolResult(content, out.facts, False, portfolio_id, out.shared, out.extra)
