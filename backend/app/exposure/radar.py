"""Radar de riesgos y oportunidades (`SPEC.md` §8.5): reglas puras, sin BD. Todo en `Decimal`.

Cada regla devuelve un `Finding` con la cifra y los datos que usan las plantillas
(`templates.py`). Invariante de producto: una oportunidad siempre lleva `user_rule`, la regla del
propio usuario (su plan o su plan de aportaciones) frente a la que se expresa. Criterios en D-078.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import ROUND_CEILING, ROUND_HALF_EVEN, Decimal
from typing import Any

from app.schemas.common import AssetClass, AssetType
from app.schemas.radar import RadarKind, RadarRule, UserRule

SINGLE_COMPANY_LIMIT = Decimal("0.05")
TOP_N = 10
TOP_N_LIMIT = Decimal("0.25")
NON_EUR_LIMIT = Decimal("0.50")
CHEAPER_DROP = Decimal("-0.03")

EUR = "EUR"
UNKNOWN_CURRENCY = "OTHER"
_NON_COMPANY_PREFIXES = ("OTROS_", "GOV_", "BONOS_")
_CENT = Decimal("0.01")


@dataclass(frozen=True)
class CompanyWeight:
    key: str
    name: str
    weight: Decimal
    """Fracción del patrimonio, con el look-through hecho."""


@dataclass(frozen=True)
class PositionIn:
    asset_id: str
    name: str
    asset_type: AssetType
    asset_class: AssetClass
    transferable: bool
    unrealized_pnl_eur: Decimal


@dataclass(frozen=True)
class AllocationIn:
    asset_id: str
    name: str
    asset_class: AssetClass
    weight: Decimal
    price_now: Decimal | None = None
    price_at_last: Decimal | None = None
    """Precio el día de la última aportación; `None` si no se conoce."""


@dataclass(frozen=True)
class DcaIn:
    """Plan de aportaciones activo."""

    plan_id: str
    amount_eur: Decimal
    allocations: tuple[AllocationIn, ...]


@dataclass(frozen=True)
class RadarInput:
    portfolio_id: str
    total_eur: Decimal
    companies: Sequence[CompanyWeight]
    currencies: Mapping[str, Decimal]
    """`by_currency` del look-through: `{código: fracción}`."""
    equity_weight: Decimal
    equity_target: Decimal
    drift_threshold: Decimal
    positions: Sequence[PositionIn]
    dca_plans: Sequence[DcaIn]


@dataclass(frozen=True)
class Finding:
    rule: RadarRule
    kind: RadarKind
    weight: Decimal | None
    value_eur: Decimal | None
    user_rule: UserRule | None = None
    ref: str = ""
    """Sufijo del id cuando una regla puede dar varios avisos (un activo del DCA)."""
    facts: dict[str, Any] = field(default_factory=dict)


def _eur(value: Decimal) -> Decimal:
    return value.quantize(_CENT, rounding=ROUND_HALF_EVEN)


def _is_company(key: str) -> bool:
    return not key.startswith(_NON_COMPANY_PREFIXES)


def _concentration(data: RadarInput) -> list[Finding]:
    """Una empresa > 5 % O las 10 mayores > 25 %: un solo aviso aunque salten las dos."""
    companies = sorted(
        (c for c in data.companies if _is_company(c.key)), key=lambda c: c.weight, reverse=True
    )
    if not companies:
        return []
    top = companies[0]
    top_n = sum((c.weight for c in companies[:TOP_N]), Decimal(0))
    single, group = top.weight > SINGLE_COMPANY_LIMIT, top_n > TOP_N_LIMIT
    if not (single or group):
        return []
    weight = top.weight if single else top_n
    return [
        Finding(
            RadarRule.CONCENTRATION,
            RadarKind.RISK,
            weight,
            _eur(weight * data.total_eur),
            facts={
                "top_name": top.name,
                "top_weight": top.weight,
                "top10_weight": top_n,
                "single_fired": single,
                "top10_fired": group,
            },
        )
    ]


def _currency(data: RadarInput) -> list[Finding]:
    """No EUR > 50 %. La divisa desconocida (`OTHER`) no cuenta: no se afirma lo que no se sabe."""
    foreign = {
        code: weight
        for code, weight in data.currencies.items()
        if code not in (EUR, UNKNOWN_CURRENCY)
    }
    total = sum(foreign.values(), Decimal(0))
    if total <= NON_EUR_LIMIT:
        return []
    main, main_weight = max(foreign.items(), key=lambda item: item[1])
    return [
        Finding(
            RadarRule.CURRENCY,
            RadarKind.RISK,
            total,
            _eur(total * data.total_eur),
            facts={"top_currency": main, "top_currency_weight": main_weight},
        )
    ]


def _drift(data: RadarInput, drift: Decimal) -> Finding:
    return Finding(
        RadarRule.DRIFT,
        RadarKind.RISK,
        drift,
        _eur(abs(drift) * data.total_eur),
        facts={
            "equity": data.equity_weight,
            "target": data.equity_target,
            "threshold": data.drift_threshold,
            "direction": "over" if drift > 0 else "under",
        },
    )


def _rebalance(data: RadarInput, drift: Decimal) -> list[Finding]:
    """Meses de aportaciones que llevan la renta variable al objetivo del plan.

    Con `E` la renta variable, `T` el patrimonio, `t` el objetivo y `c`, `c_e` lo que aporta el plan
    cada mes en total y a renta variable: `E + n·c_e = t·(T + n·c)`, luego `n = (E − t·T) / (t·c −
    c_e)`. Solo hay solución si las aportaciones empujan hacia el lado correcto.
    """
    target = data.equity_target
    gap = drift * data.total_eur  # E − t·T
    best: tuple[int, DcaIn] | None = None
    for plan in data.dca_plans:
        to_equity = plan.amount_eur * sum(
            (a.weight for a in plan.allocations if a.asset_class is AssetClass.EQUITY), Decimal(0)
        )
        pull = target * plan.amount_eur - to_equity
        if pull == 0 or (gap > 0) != (pull > 0):
            continue
        months = int((gap / pull).to_integral_value(rounding=ROUND_CEILING))
        if best is None or months < best[0]:
            best = (months, plan)
    if best is None:
        return []
    months, plan = best
    return [
        Finding(
            RadarRule.REBALANCE_WITH_DCA,
            RadarKind.OPPORTUNITY,
            drift,
            _eur(abs(gap)),
            UserRule(source="dca_plan", ref=plan.plan_id),
            facts={
                "months": months,
                "monthly_eur": plan.amount_eur,
                "target_class": AssetClass.FIXED_INCOME if gap > 0 else AssetClass.EQUITY,
            },
        )
    ]


def _cheaper(data: RadarInput) -> list[Finding]:
    """El activo de una aportación cotiza > 3 % por debajo del día de la última aportación."""
    findings: list[Finding] = []
    for plan in data.dca_plans:
        for line in plan.allocations:
            if not line.price_now or not line.price_at_last or line.price_at_last <= 0:
                continue
            change = line.price_now / line.price_at_last - 1
            if change >= CHEAPER_DROP:
                continue
            amount = _eur(plan.amount_eur * line.weight)
            findings.append(
                Finding(
                    RadarRule.CHEAPER_CONTRIBUTION,
                    RadarKind.OPPORTUNITY,
                    change,
                    amount,
                    UserRule(source="dca_plan", ref=plan.plan_id),
                    ref=line.asset_id,
                    facts={"asset_name": line.name, "drop": change, "amount_eur": amount},
                )
            )
    return findings


def _tax_free_transfer(data: RadarInput, drift: Decimal) -> list[Finding]:
    """Con desviación: fondo traspasable con plusvalía en la clase sobreponderada y fondo
    traspasable en la infraponderada. La regla del usuario es su plan (D-078)."""
    over = drift > 0
    origin_class = AssetClass.EQUITY if over else AssetClass.FIXED_INCOME
    destination_class = AssetClass.FIXED_INCOME if over else AssetClass.EQUITY
    movable = [p for p in data.positions if p.transferable]
    origins = [p for p in movable if p.asset_class is origin_class and p.unrealized_pnl_eur > 0]
    destinations = [p for p in movable if p.asset_class is destination_class]
    if not origins or not destinations:
        return []
    gain = sum((p.unrealized_pnl_eur for p in origins), Decimal(0))
    return [
        Finding(
            RadarRule.TAX_FREE_TRANSFER,
            RadarKind.OPPORTUNITY,
            drift,
            _eur(gain),
            UserRule(source="plan", ref=data.portfolio_id),
            facts={
                "origin_names": tuple(p.name for p in origins),
                "destination_names": tuple(p.name for p in destinations),
                "origin_class": origin_class,
                "destination_class": destination_class,
            },
        )
    ]


def evaluate(data: RadarInput) -> list[Finding]:
    """Los avisos de la cartera, riesgos antes que oportunidades, en el orden de `RadarRule`."""
    if data.total_eur <= 0:
        return []
    drift = data.equity_weight - data.equity_target
    drifted = abs(drift) > data.drift_threshold
    findings = [*_concentration(data), *_currency(data)]
    if drifted:
        findings += [_drift(data, drift), *_rebalance(data, drift)]
    findings += _cheaper(data)
    if drifted:
        findings += _tax_free_transfer(data, drift)
    return findings
