"""`impact/engine.py`: fórmulas de `SPEC.md` §8.2 con casos calculados a mano."""

from collections.abc import Mapping
from datetime import date
from decimal import Decimal as D

import pytest

from app.impact.betas import BetaEstimate
from app.impact.engine import (
    AssetResult,
    ImpactResult,
    PositionIn,
    ShocksIn,
    closing_link,
    compute_impact,
    polarity,
    surprise_label,
)
from app.impact.scenario import estimate
from app.schemas.common import AssetClass, Confidence, Factor, Polarity
from app.schemas.impact import SurpriseLabel

EQ = Factor.EQ_GLOBAL
TECH = Factor.EQ_US_TECH
RATES = Factor.RATES_EUR
FX = Factor.EURUSD
FI = AssetClass.FIXED_INCOME
EQUITY = AssetClass.EQUITY


def beta(factor: Factor, value: str, se: str = "0.01", r2: str = "0.8") -> BetaEstimate:
    return BetaEstimate(
        asset_id="A",
        factor=factor,
        beta=D(value),
        std_err=D(se),
        r2=D(r2),
        n_obs=700,
        window_start=date(2023, 11, 7),
        window_end=date(2026, 11, 6),
    )


def position(
    *betas: BetaEstimate,
    asset_id: str = "A",
    value: str = "1000",
    currency: str = "EUR",
    asset_class: AssetClass = EQUITY,
    weights: Mapping[str, D] | None = None,
) -> PositionIn:
    return PositionIn(
        asset_id=asset_id,
        name=asset_id,
        asset_class=asset_class,
        currency=currency,
        value_eur=D(value),
        betas=betas,
        company_weights=weights or {},
    )


def shocks(factors: Mapping[Factor, str], moves: Mapping[str, str] | None = None) -> ShocksIn:
    return ShocksIn(
        factor_shocks={f: D(s) for f, s in factors.items()},
        company_moves={k: D(m) for k, m in (moves or {}).items()},
        labels={},
    )


def one(result: ImpactResult) -> AssetResult:
    assert len(result.assets) == 1
    return result.assets[0]


def split(asset: AssetResult) -> tuple[D, D, D]:
    return asset.impact_eur, asset.market_eur, asset.fx_eur


def test_market_effect_is_sum_of_beta_times_shock() -> None:
    result = compute_impact(
        [position(beta(EQ, "0.5"), beta(TECH, "0.25"))],
        shocks({EQ: "0.02", TECH: "0.04"}),
        D("1"),
    )
    assert split(one(result)) == (D("20.00"), D("20.00"), D("0.00"))
    assert result.impact_eur == D("20.00")


def test_factor_without_shock_is_ignored() -> None:
    result = compute_impact([position(beta(EQ, "1"))], shocks({TECH: "0.04"}), D("1"))
    assert result.impact_eur == D("0.00")


def test_usd_asset_splits_market_and_currency() -> None:
    # (1 + 0,01) · 1/(1 + 0,01) − 1 = 0: lo que gana en bolsa lo pierde en dólar.
    result = compute_impact(
        [position(beta(EQ, "1"), currency="USD")], shocks({EQ: "0.01", FX: "0.01"}), D("1")
    )
    assert split(one(result)) == (D("0.00"), D("10.00"), D("-10.00"))


def test_eur_asset_gets_no_translation_effect() -> None:
    result = compute_impact([position(beta(EQ, "1"))], shocks({FX: "0.05"}), D("1"))
    assert one(result).impact_eur == D("0.00")


def test_eur_asset_with_dollar_beta_shows_it_as_currency() -> None:
    result = compute_impact([position(beta(FX, "-0.5"))], shocks({FX: "0.02"}), D("1"))
    assert split(one(result)) == (D("-10.00"), D("0.00"), D("-10.00"))
    assert one(result).channel == "dólar"


def test_earnings_apply_factors_only_to_the_rest_of_the_fund() -> None:
    # 0,05 · (−0,10) + 0,95 · 1 · (−0,02) = −0,024
    result = compute_impact(
        [position(beta(EQ, "1"), weights={"NVDA": D("0.05")})],
        shocks({EQ: "-0.02"}, {"NVDA": "-0.10"}),
        D("1"),
    )
    assert one(result).impact_eur == D("-24.00")
    assert one(result).channel == "bolsa"


def test_direct_stock_takes_the_company_move_and_no_factor() -> None:
    result = compute_impact(
        [position(beta(EQ, "1"), weights={"NVDA": D("1")})],
        shocks({EQ: "-0.02"}, {"NVDA": "-0.10"}),
        D("1"),
    )
    assert one(result).impact_eur == D("-100.00")
    assert one(result).channel == "resultados NVDA"
    assert (result.low_eur, result.high_eur) == (D("-100.00"), D("-100.00"))


def test_company_absent_from_asset_leaves_factors_whole() -> None:
    result = compute_impact(
        [position(beta(EQ, "1"))], shocks({EQ: "-0.02"}, {"NVDA": "-0.10"}), D("1")
    )
    assert one(result).impact_eur == D("-20.00")


def test_noisy_beta_widens_range_but_not_impact() -> None:
    # |0,5 / 0,3| < 2. Semiancho: 1,28 · 1000 · (0,3 + 0,5) · 0,02 = 20,48
    result = compute_impact([position(beta(EQ, "0.5", se="0.3"))], shocks({EQ: "0.02"}), D("1"))
    assert result.impact_eur == D("0.00")
    assert (result.low_eur, result.high_eur) == (D("-20.48"), D("20.48"))


def test_beta_at_two_standard_errors_counts() -> None:
    result = compute_impact([position(beta(EQ, "0.5", se="0.25"))], shocks({EQ: "0.02"}), D("1"))
    assert result.impact_eur == D("10.00")


def test_range_treats_assets_as_independent() -> None:
    # Términos 3 y 4 → sqrt(25) = 5 → ± 6,40
    result = compute_impact(
        [
            position(beta(EQ, "1", se="0.15"), asset_id="A"),
            position(beta(EQ, "1", se="0.20"), asset_id="B"),
        ],
        shocks({EQ: "0.02"}),
        D("1"),
    )
    assert result.impact_eur == D("40.00")
    assert (result.low_eur, result.high_eur) == (D("33.60"), D("46.40"))


def test_opposite_shocks_do_not_cancel_the_error() -> None:
    # 1000 · (0,1 · 0,02 + 0,1 · 0,02) = 4 → ± 5,12
    result = compute_impact(
        [position(beta(EQ, "1", se="0.1"), beta(TECH, "1", se="0.1"))],
        shocks({EQ: "0.02", TECH: "-0.02"}),
        D("1"),
    )
    assert (result.low_eur, result.high_eur) == (D("-5.12"), D("5.12"))


def test_breakdown_adds_up_to_the_total() -> None:
    positions = [
        position(beta(EQ, "0.333333"), asset_id="A", value="1000.01"),
        position(beta(EQ, "0.333333"), asset_id="B", value="1000.02"),
        position(beta(EQ, "0.333333"), asset_id="C", value="1000.04"),
    ]
    result = compute_impact(positions, shocks({EQ: "0.0123"}), D("1"))
    assert sum(a.impact_eur for a in result.assets) == result.impact_eur
    for asset in result.assets:
        assert asset.market_eur + asset.fx_eur == asset.impact_eur


def test_position_without_betas_has_no_effect() -> None:
    result = compute_impact([position(asset_class=AssetClass.CASH)], shocks({EQ: "0.02"}), D("1"))
    assert one(result).impact_eur == D("0.00")
    assert one(result).channel == "sin efecto"


def test_channel_uses_the_analyzer_label() -> None:
    labelled = ShocksIn({RATES: D("-0.001")}, {}, {RATES: "tipos del BCE"})
    result = compute_impact([position(beta(RATES, "-5", se="1"))], labelled, D("1"))
    assert one(result).channel == "tipos del BCE"


@pytest.mark.parametrize(
    ("r2", "coverage", "expected"),
    [
        ("0.6", "0.9", Confidence.ALTA),
        ("0.6", "0.89", Confidence.MEDIA),
        ("0.59", "1", Confidence.MEDIA),
        ("0.3", "0.5", Confidence.MEDIA),
        ("0.29", "1", Confidence.BAJA),
    ],
)
def test_confidence_thresholds(r2: str, coverage: str, expected: Confidence) -> None:
    result = compute_impact([position(beta(EQ, "1", r2=r2))], shocks({EQ: "0.01"}), D(coverage))
    assert result.confidence is expected


def test_assets_without_betas_count_as_zero_r2() -> None:
    # (1000 · 0,8 + 1000 · 0) / 2000 = 0,4
    result = compute_impact(
        [position(beta(EQ, "1"), asset_id="A"), position(asset_id="DEP")],
        shocks({EQ: "0.01"}),
        D("1"),
    )
    assert result.r2 == D("0.4")
    assert result.confidence is Confidence.MEDIA


def test_empty_portfolio_is_zero_with_low_confidence() -> None:
    result = compute_impact([], shocks({EQ: "0.01"}), D("1"))
    assert result.impact_eur == D("0.00")
    assert result.confidence is Confidence.BAJA


def _result(low: str, high: str, *assets: tuple[AssetClass, str]) -> ImpactResult:
    rows = [
        AssetResult(f"A{i}", "n", cls, D("1000"), D(eur), D(eur), D("0"), "bolsa")
        for i, (cls, eur) in enumerate(assets)
    ]
    return ImpactResult(
        impact_eur=sum((r.impact_eur for r in rows), D("0")),
        low_eur=D(low),
        high_eur=D(high),
        r2=D("0.8"),
        confidence=Confidence.ALTA,
        assets=rows,
    )


def test_risk_when_whole_range_is_negative() -> None:
    assert polarity(_result("-50", "-1", (EQUITY, "-20")), {EQUITY}) is Polarity.RIESGO


def test_opportunity_when_most_gain_is_in_an_underweight_class() -> None:
    assert polarity(_result("1", "90", (FI, "60"), (EQUITY, "40")), {FI}) is Polarity.OPORTUNIDAD


def test_exactly_half_is_not_opportunity() -> None:
    assert polarity(_result("1", "90", (FI, "50"), (EQUITY, "50")), {FI}) is Polarity.NEUTRAL


def test_gain_in_overweight_class_is_neutral() -> None:
    assert polarity(_result("1", "90", (EQUITY, "60")), {FI}) is Polarity.NEUTRAL


def test_range_crossing_zero_is_neutral() -> None:
    assert polarity(_result("-1", "90", (FI, "60")), {FI}) is Polarity.NEUTRAL


def test_closing_link_names_the_class_with_largest_move() -> None:
    result = _result("0", "0", (FI, "60"), (EQUITY, "-90"), (EQUITY, "10"))
    assert closing_link(result) == "Bajan tus posiciones de renta variable"
    assert closing_link(_result("0", "0", (FI, "5"))) == "Suben tus fondos de renta fija"


def test_closing_link_without_effect() -> None:
    assert closing_link(_result("0", "0", (FI, "0"))) == "Apenas cambia tu cartera"


@pytest.mark.parametrize(
    ("metric", "expected", "actual", "label"),
    [
        ("rate_change_bp", "-25", "-25", SurpriseLabel.EN_LINEA),
        ("rate_change_bp", "-25", "-50", SurpriseLabel.MEJOR),
        ("rate_change_bp", "-25", "0", SurpriseLabel.PEOR),
        ("eps_usd", "0.8", "0.9", SurpriseLabel.MEJOR),
        ("eps_usd", "0.8", "0.7", SurpriseLabel.PEOR),
    ],
)
def test_surprise_label(metric: str, expected: str, actual: str, label: SurpriseLabel) -> None:
    assert surprise_label(metric, expected, actual) is label


def test_scenario_shares_the_engine() -> None:
    result = estimate([position(beta(EQ, "0.5"))], {EQ: D("-0.10")}, D("1"))
    assert one(result).impact_eur == D("-50.00")
    assert one(result).channel == "bolsa"
