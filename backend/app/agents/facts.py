"""Cifras ya calculadas (`Fact`) para el explicador y el guardián (diseño del MVP §4.4).

Cada `Fact` lleva su `display`, el texto que el prompt pide copiar literalmente, y su `calc_id`.
Aquí no se calcula nada: solo se copian valores de los contratos de otros módulos y se formatean
en español de España ("42.380 euros", "61 %", "0,25 %"). Funciones puras.
"""

from decimal import Decimal

from app.agents.fact_format import fraction, money, number, year
from app.schemas.agents import EventImpactStub, Fact, StatusFacts
from app.schemas.exposure import ExposureOut
from app.schemas.impact import EventImpactOut, MoveAttributionOut, ScenarioOut
from app.schemas.planning import ProjectionOut
from app.schemas.portfolio import PlanOut, PortfolioOut

_TOP_ASSETS = 3


def _direction(value: Decimal) -> str:
    return "a favor" if value > 0 else "en contra" if value < 0 else "sin efecto"


# --- Contratos → facts ---


def portfolio_facts(portfolio: PortfolioOut) -> list[Fact]:
    cid = portfolio.calc_id
    week = portfolio.change_week_eur
    trend = "subida" if week > 0 else "bajada" if week < 0 else "sin cambio"
    facts = [
        money("total", "patrimonio", portfolio.total_eur, cid),
        money("change_week", f"variación semanal ({trend})", week, cid),
        fraction(
            "change_week_pct", f"variación semanal en % ({trend})", portfolio.change_week_pct, cid
        ),
        fraction(
            "allocation.equity", "peso de la renta variable", portfolio.allocation.equity, cid
        ),
        fraction(
            "allocation.fixed_income",
            "peso de la renta fija",
            portfolio.allocation.fixed_income,
            cid,
        ),
    ]
    for position in portfolio.positions:
        facts.append(
            money(
                f"pos.{position.asset_id}.value",
                f"valor de {position.name}",
                position.value_eur,
                cid,
            )
        )
    return facts


def plan_facts(plan: PlanOut) -> list[Fact]:
    cid = plan.calc_id
    facts = [
        fraction("plan.equity_target", "renta variable objetivo del plan", plan.target.equity, cid),
        fraction("plan.equity_current", "renta variable actual", plan.current.equity, cid),
        fraction(
            "plan.drift_equity",
            "desviación de la renta variable frente al plan",
            plan.drift_equity,
            cid,
        ),
        fraction(
            "plan.drift_threshold", "umbral de desviación del plan", plan.drift_threshold, cid
        ),
    ]
    if plan.goal_amount_eur is not None:
        facts.append(money("plan.goal_amount", "objetivo de patrimonio", plan.goal_amount_eur, cid))
    if plan.goal_year is not None:
        facts.append(year("plan.goal_year", "año del objetivo", plan.goal_year, cid))
    return facts


def projection_facts(projection: ProjectionOut) -> list[Fact]:
    cid = projection.calc_id
    facts = [
        money("projection.goal_amount", "objetivo de patrimonio", projection.goal_amount_eur, cid),
        year("projection.goal_year", "año del objetivo", projection.goal_year, cid),
        money(
            "projection.monthly_contribution",
            "aportación mensual (DCA)",
            projection.monthly_contribution_eur,
            cid,
        ),
        money(
            "projection.gap",
            "lo que falta en el escenario base para la meta",
            projection.gap_eur,
            cid,
        ),
    ]
    for scenario in projection.scenarios:
        facts.append(
            money(
                f"projection.{scenario.name}.value_at_goal",
                f"valor estimado en el año del objetivo (escenario {scenario.name})",
                scenario.value_at_goal_eur,
                cid,
            )
        )
    return facts


def event_impact_facts(event: EventImpactOut) -> list[Fact]:
    cid, prefix = event.calc_id, f"evt.{event.event_id}"
    facts = [
        money(
            f"{prefix}.impact",
            f"impacto estimado de «{event.title}» ({_direction(event.impact_eur)})",
            event.impact_eur,
            cid,
        ),
        money(f"{prefix}.low", f"extremo bajo del rango de «{event.title}»", event.low_eur, cid),
        money(f"{prefix}.high", f"extremo alto del rango de «{event.title}»", event.high_eur, cid),
        fraction(
            f"{prefix}.impact_pct",
            f"impacto de «{event.title}» sobre el patrimonio",
            event.impact_pct,
            cid,
        ),
    ]
    top = sorted(event.breakdown, key=lambda a: abs(a.impact_eur), reverse=True)[:_TOP_ASSETS]
    for asset in top:
        facts.append(
            money(
                f"{prefix}.asset.{asset.asset_id}",
                f"impacto de «{event.title}» en {asset.name} (canal {asset.channel})",
                asset.impact_eur,
                cid,
            )
        )
    return facts


def exposure_facts(exposure: ExposureOut) -> list[Fact]:
    cid = exposure.calc_id
    radio = exposure.radiography
    facts = [
        number(
            "exposure.num_holdings",
            "número de empresas en las que inviertes",
            Decimal(radio.num_holdings),
            cid,
        ),
        fraction(
            "exposure.top_country",
            f"peso de {radio.top_country.label}",
            radio.top_country.weight,
            cid,
        ),
        fraction(
            "exposure.top_companies_group",
            f"peso de las {radio.top_companies_group.n} primeras empresas",
            radio.top_companies_group.weight,
            cid,
        ),
        fraction(
            "exposure.coverage",
            "parte de la cartera con composición conocida",
            exposure.coverage_pct,
            cid,
        ),
    ]
    for group, buckets in (
        ("country", exposure.by_country),
        ("sector", exposure.by_sector),
        ("currency", exposure.by_currency),
    ):
        for bucket in buckets:
            facts.append(
                fraction(
                    f"exposure.{group}.{bucket.key}", f"peso de {bucket.label}", bucket.weight, cid
                )
            )
    for company in exposure.top_companies:
        facts.append(
            fraction(
                f"exposure.company.{company.key}", f"peso de {company.name}", company.weight, cid
            )
        )
    return facts


def scenario_facts(scenario: ScenarioOut) -> list[Fact]:
    cid = scenario.calc_id
    facts = [
        money(
            "scenario.impact",
            f"impacto estimado del escenario ({_direction(scenario.impact_eur)})",
            scenario.impact_eur,
            cid,
        ),
        money("scenario.low", "extremo bajo del rango del escenario", scenario.low_eur, cid),
        money("scenario.high", "extremo alto del rango del escenario", scenario.high_eur, cid),
    ]
    for factor, shock in scenario.factor_shocks.items():
        facts.append(
            fraction(f"scenario.shock.{factor}", f"movimiento supuesto de {factor}", shock, cid)
        )
    return facts


def move_facts(move: MoveAttributionOut) -> list[Fact]:
    cid = move.calc_id
    trend = "subida" if move.change_eur > 0 else "bajada" if move.change_eur < 0 else "sin cambio"
    facts = [
        money("move.change", f"variación del periodo ({trend})", move.change_eur, cid),
        fraction("move.change_pct", f"variación del periodo en % ({trend})", move.change_pct, cid),
        money(
            "move.unexplained",
            "parte de la variación sin evento asociado",
            move.unexplained_eur,
            cid,
        ),
    ]
    for item in move.by_asset:
        facts.append(
            money(f"move.asset.{item.asset_id}", f"variación de {item.name}", item.change_eur, cid)
        )
    for event in move.by_event:
        facts.append(
            money(
                f"move.event.{event.event_id}",
                f"efecto estimado de «{event.title}»",
                event.impact_eur,
                cid,
            )
        )
    return facts


def status_facts(facts: StatusFacts) -> list[Fact]:
    cid = facts.calc_id
    out = [
        money("total", "patrimonio", facts.total_eur, cid),
        fraction("change_week_pct", "variación semanal en %", facts.change_week_pct, cid),
    ]
    if facts.event_impact_eur is not None:
        out.append(
            money(
                "event.impact",
                f"impacto del evento ({_direction(facts.event_impact_eur)})",
                facts.event_impact_eur,
                cid,
            )
        )
    if facts.equity_current is not None:
        out.append(
            fraction("plan.equity_current", "renta variable actual", facts.equity_current, cid)
        )
    if facts.equity_target is not None:
        out.append(
            fraction("plan.equity_target", "renta variable objetivo", facts.equity_target, cid)
        )
    return out


def stub_facts(impact: EventImpactStub) -> list[Fact]:
    cid = impact.calc_id
    facts = [
        money(
            "impact", f"impacto estimado ({_direction(impact.impact_eur)})", impact.impact_eur, cid
        ),
        money("low", "extremo bajo del rango", impact.low_eur, cid),
        money("high", "extremo alto del rango", impact.high_eur, cid),
    ]
    top = sorted(impact.breakdown, key=lambda a: abs(a.impact_eur), reverse=True)[:_TOP_ASSETS]
    for asset in top:
        facts.append(
            money(f"asset.{asset.asset_id}", f"impacto en {asset.name}", asset.impact_eur, cid)
        )
    return facts
