"""Motor de impacto (`SPEC.md` §8.2): funciones puras, sin BD. Todo en `Decimal`.

Decisiones que concretan la fórmula: D-050 (betas no significativas, activos sin betas) y D-XXX
(`se·|s|` en el rango y efecto dólar de los activos en EUR).
"""

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import ROUND_HALF_EVEN, Decimal

from app.impact.betas import BetaEstimate
from app.schemas.common import AssetClass, Confidence, Factor, Polarity
from app.schemas.impact import SurpriseLabel

FORMULA = (
    "I_i = V_i · ((1 + r_i)(1 + r_fx) − 1); "
    "r_i = Σ_c w_c · m_c + (1 − Σ_c w_c) · Σ_f β_f · s_f (solo β con |β/se| ≥ 2); "
    "r_fx = 1/(1 + s_EURUSD) − 1 si el activo cotiza en USD; "
    "rango = I ± 1,28 · sqrt(Σ_i (V_i · (1 − Σ_c w_c) · Σ_f u_f)²), "
    "u_f = se_f · |s_f| y, si β no es significativa, además |β_f · s_f|; "
    "los errores de cada activo se tratan como independientes"
)

ZERO = Decimal("0")
ONE = Decimal("1")
_CENT = Decimal("0.01")
_Z_80 = Decimal("1.28")
_MIN_T = Decimal("2")
_R2_HIGH = Decimal("0.6")
_R2_MEDIUM = Decimal("0.3")
_COVERAGE_HIGH = Decimal("0.9")
_MAJORITY = Decimal("0.5")

NO_EFFECT = "sin efecto"
DEFAULT_LABELS: Mapping[Factor, str] = {
    Factor.EQ_GLOBAL: "bolsa",
    Factor.EQ_US_TECH: "tecnológicas",
    Factor.RATES_EUR: "tipos",
    Factor.OIL: "petróleo",
    Factor.EURUSD: "dólar",
}
_CLASS_NAMES: Mapping[AssetClass, str] = {
    AssetClass.EQUITY: "tus posiciones de renta variable",
    AssetClass.FIXED_INCOME: "tus fondos de renta fija",
    AssetClass.CASH: "tus depósitos",
    AssetClass.MIXED: "tus activos mixtos",
}
_LOWER_IS_BETTER = {"rate_change_bp"}


@dataclass(frozen=True)
class PositionIn:
    """`company_weights`: peso de cada empresa en el activo (1 si es acción directa)."""

    asset_id: str
    name: str
    asset_class: AssetClass
    currency: str
    value_eur: Decimal
    betas: Sequence[BetaEstimate] = ()
    company_weights: Mapping[str, Decimal] = field(default_factory=dict)


@dataclass(frozen=True)
class ShocksIn:
    """`labels`: etiqueta de cada factor según el analizador. Si falta, `DEFAULT_LABELS`."""

    factor_shocks: Mapping[Factor, Decimal]
    company_moves: Mapping[str, Decimal]
    labels: Mapping[Factor, str]


@dataclass(frozen=True)
class AssetResult:
    asset_id: str
    name: str
    asset_class: AssetClass
    value_eur: Decimal
    impact_eur: Decimal
    market_eur: Decimal
    fx_eur: Decimal
    channel: str


@dataclass(frozen=True)
class ImpactResult:
    impact_eur: Decimal
    low_eur: Decimal
    high_eur: Decimal
    r2: Decimal
    confidence: Confidence
    assets: list[AssetResult]


def _cents(value: Decimal) -> Decimal:
    return value.quantize(_CENT, rounding=ROUND_HALF_EVEN)


def _is_significant(beta: BetaEstimate) -> bool:
    return abs(beta.beta) >= _MIN_T * beta.std_err


def _channel(contributions: Sequence[tuple[str, Decimal]]) -> str:
    label, size = max(contributions, key=lambda c: abs(c[1]), default=(NO_EFFECT, ZERO))
    return label if size != ZERO else NO_EFFECT


def _position_impact(position: PositionIn, shocks: ShocksIn) -> tuple[AssetResult, Decimal]:
    """Resultado del activo y su término de incertidumbre en euros."""
    weights = position.company_weights
    company_r = {key: weights.get(key, ZERO) * m for key, m in sorted(shocks.company_moves.items())}
    rest = ONE - min(ONE, sum((weights.get(key, ZERO) for key in shocks.company_moves), ZERO))

    factor_r: dict[Factor, Decimal] = {}
    uncertainty = ZERO
    for beta in sorted(position.betas, key=lambda b: b.factor.value):
        shock = shocks.factor_shocks.get(beta.factor)
        if shock is None:
            continue
        uncertainty += beta.std_err * abs(shock)
        if _is_significant(beta):
            factor_r[beta.factor] = beta.beta * shock * rest
        else:
            uncertainty += abs(beta.beta * shock)

    dollar = shocks.factor_shocks.get(Factor.EURUSD)
    r_fx = ONE / (ONE + dollar) - ONE if dollar is not None and position.currency == "USD" else ZERO
    beta_fx = factor_r.pop(Factor.EURUSD, ZERO)
    r_market = sum(company_r.values(), ZERO) + sum(factor_r.values(), ZERO)
    r_total = r_market + beta_fx

    impact = _cents(position.value_eur * ((ONE + r_total) * (ONE + r_fx) - ONE))
    market = _cents(position.value_eur * r_market)
    contributions = [(f"resultados {key}", r) for key, r in company_r.items()]
    contributions += [(shocks.labels.get(f, DEFAULT_LABELS[f]), r) for f, r in factor_r.items()]
    contributions.append(
        (shocks.labels.get(Factor.EURUSD, DEFAULT_LABELS[Factor.EURUSD]), beta_fx + r_fx)
    )
    result = AssetResult(
        asset_id=position.asset_id,
        name=position.name,
        asset_class=position.asset_class,
        value_eur=position.value_eur,
        impact_eur=impact,
        market_eur=market,
        fx_eur=impact - market,
        channel=_channel(contributions),
    )
    return result, position.value_eur * rest * uncertainty


def _confidence(r2: Decimal, coverage: Decimal) -> Confidence:
    if r2 >= _R2_HIGH and coverage >= _COVERAGE_HIGH:
        return Confidence.ALTA
    return Confidence.MEDIA if r2 >= _R2_MEDIUM else Confidence.BAJA


def _weighted_r2(positions: Sequence[PositionIn]) -> Decimal:
    """R² medio ponderado por valor. Un activo sin betas cuenta como 0 (D-050)."""
    total = sum((p.value_eur for p in positions), ZERO)
    if total == ZERO:
        return ZERO
    weighted = sum((p.value_eur * p.betas[0].r2 for p in positions if p.betas), ZERO)
    return weighted / total


def compute_impact(
    positions: Sequence[PositionIn], shocks: ShocksIn, coverage: Decimal
) -> ImpactResult:
    """Impacto por activo y total. El total es la suma de lo que se muestra por activo."""
    rows = [_position_impact(position, shocks) for position in positions]
    impact = sum((asset.impact_eur for asset, _ in rows), ZERO).quantize(_CENT)
    half_width = _Z_80 * sum((term * term for _, term in rows), ZERO).sqrt()
    r2 = _weighted_r2(positions)
    return ImpactResult(
        impact_eur=impact,
        low_eur=_cents(impact - half_width),
        high_eur=_cents(impact + half_width),
        r2=r2,
        confidence=_confidence(r2, coverage),
        assets=[asset for asset, _ in rows],
    )


def polarity(result: ImpactResult, under_target: Collection[AssetClass]) -> Polarity:
    """`oportunidad` exige que el evento acerque la cartera al plan del usuario (§4.3)."""
    if result.high_eur < ZERO:
        return Polarity.RIESGO
    if result.low_eur <= ZERO:
        return Polarity.NEUTRAL
    gains: dict[AssetClass, Decimal] = {}
    for asset in result.assets:
        if asset.impact_eur > ZERO:
            gains[asset.asset_class] = gains.get(asset.asset_class, ZERO) + asset.impact_eur
    total = sum(gains.values(), ZERO)
    if any(gain > total * _MAJORITY for cls, gain in gains.items() if cls in under_target):
        return Polarity.OPORTUNIDAD
    return Polarity.NEUTRAL


def closing_link(result: ImpactResult) -> str:
    """Último eslabón de la cadena causal: la clase de activo con mayor |impacto|."""
    by_class: dict[AssetClass, Decimal] = {}
    for asset in result.assets:
        by_class[asset.asset_class] = by_class.get(asset.asset_class, ZERO) + asset.impact_eur
    cls, impact = max(by_class.items(), key=lambda c: abs(c[1]), default=(None, ZERO))
    if cls is None or impact == ZERO:
        return "Apenas cambia tu cartera"
    return f"{'Suben' if impact > ZERO else 'Bajan'} {_CLASS_NAMES[cls]}"


def surprise_label(metric: str, expected: str, actual: str) -> SurpriseLabel:
    gap = Decimal(actual) - Decimal(expected)
    if gap == ZERO:
        return SurpriseLabel.EN_LINEA
    better = gap < ZERO if metric in _LOWER_IS_BETTER else gap > ZERO
    return SurpriseLabel.MEJOR if better else SurpriseLabel.PEOR
