"""Definiciones de las herramientas del explicador para la API de Claude (`tools.py`).

Todas, salvo `list_portfolios`, aceptan `portfolio_id`: el asistente puede consultar cualquier
cartera del usuario (T4-14). Sin `portfolio_id`, la de la pregunta o la elegida en la app.
"""

from typing import Any, get_args

from app.schemas.common import Factor
from app.schemas.impact import MovePeriod
from app.schemas.news import NewsCategory

MAX_DAYS = 30
MAX_NEWS = 20
PERIODS: tuple[str, ...] = get_args(MovePeriod)
_FACTORS = [factor.value for factor in Factor]
_PORTFOLIO = {
    "type": "string",
    "description": "id de la cartera (de `list_portfolios`). Sin él, la cartera de la pregunta "
    "o la elegida en la app.",
}


def _schema(properties: dict[str, Any] | None = None, required: list[str] | None = None) -> Any:
    return {
        "type": "object",
        "properties": properties or {},
        "required": required or [],
        "additionalProperties": False,
    }


def _per_portfolio(
    properties: dict[str, Any] | None = None, required: list[str] | None = None
) -> Any:
    return _schema({"portfolio_id": _PORTFOLIO, **(properties or {})}, required)


DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "list_portfolios",
        "description": "Carteras del usuario con su id, nombre, tipo y perfil. Cada cartera es "
        "independiente: nunca se suman sus cifras.",
        "input_schema": _schema(),
    },
    {
        "name": "get_portfolio",
        "description": "Cartera valorada: patrimonio, variación semanal, asignación y posiciones.",
        "input_schema": _per_portfolio(),
    },
    {
        "name": "get_status",
        "description": "Estado de la cartera (tranquilo, atento, revisa el plan) y por qué.",
        "input_schema": _per_portfolio(),
    },
    {
        "name": "get_exposure",
        "description": "Exposición real por país, sector, divisa y empresa (look-through de los "
        "fondos), solapamientos y radiografía.",
        "input_schema": _per_portfolio(),
    },
    {
        "name": "get_events",
        "description": "Eventos de los últimos `days` días con su impacto estimado en la cartera, "
        "rango, confianza y desglose por activo.",
        "input_schema": _per_portfolio(
            {"days": {"type": "integer", "minimum": 1, "maximum": MAX_DAYS}}, ["days"]
        ),
    },
    {
        "name": "get_news",
        "description": "Noticias recientes vistas desde la cartera, con su impacto estimado o "
        "medido en ella (rango en euros y %, plazo, confianza). Con `affecting` (por defecto), "
        "solo las que le afectan.",
        "input_schema": _per_portfolio(
            {
                "category": {"type": "string", "enum": [c.value for c in NewsCategory]},
                "affecting": {"type": "boolean"},
                "limit": {"type": "integer", "minimum": 1, "maximum": MAX_NEWS},
            }
        ),
    },
    {
        "name": "get_news_item",
        "description": "Una noticia concreta (por su id) con su impacto en la cartera.",
        "input_schema": _per_portfolio({"news_id": {"type": "string"}}, ["news_id"]),
    },
    {
        "name": "get_alerts",
        "description": "Avisos que ha recibido la cartera (eventos, noticias, movimientos del "
        "mercado, aportaciones pendientes), del más reciente al más antiguo.",
        "input_schema": _per_portfolio(),
    },
    {
        "name": "get_radar",
        "description": "Radar de la cartera: riesgos (concentración, divisa, desviación) y "
        "oportunidades frente a las reglas del propio usuario.",
        "input_schema": _per_portfolio(),
    },
    {
        "name": "get_agenda",
        "description": "Próximas citas que pueden mover la cartera (reuniones de bancos "
        "centrales, resultados, aportaciones) y cuánto de la cartera está expuesto.",
        "input_schema": _per_portfolio(),
    },
    {
        "name": "estimate_impact",
        "description": "Impacto estimado de un escenario hipotético que plantea el usuario («¿y "
        "si el petróleo sube…?»). Cada `shock` es la fracción que dice el usuario (−0.10 = −10 "
        "%). Usa solo movimientos que el usuario haya dicho: no los inventes.",
        "input_schema": _per_portfolio(
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
        "input_schema": _per_portfolio(),
    },
    {
        "name": "explain_move",
        "description": "Atribución del cambio de valor del periodo a activos y eventos.",
        "input_schema": _per_portfolio(
            {"period": {"type": "string", "enum": list(PERIODS)}}, ["period"]
        ),
    },
]
