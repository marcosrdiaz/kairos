"""Radar (`exposure/radar.py`, SPEC §8.5): las 6 reglas con entradas sintéticas y cálculo a mano.

Funciones puras, sin BD. Los casos con las carteras de Laura y Javier están en
`test_radar_service.py`.
"""

from decimal import Decimal

from app.exposure import radar
from app.exposure.radar import (
    AllocationIn,
    CompanyWeight,
    DcaIn,
    Finding,
    PositionIn,
    RadarInput,
)
from app.schemas.common import AssetClass, AssetType
from app.schemas.radar import RadarKind, RadarRule

D = Decimal
TOTAL = D("100000")


def _companies(*weights: str, prefix: str = "C") -> tuple[CompanyWeight, ...]:
    return tuple(CompanyWeight(f"{prefix}{i}", f"Empresa {i}", D(w)) for i, w in enumerate(weights))


def _fund(
    asset_id: str,
    asset_class: AssetClass,
    pnl: str = "0",
    *,
    transferable: bool = True,
    asset_type: AssetType = AssetType.FUND,
) -> PositionIn:
    return PositionIn(asset_id, f"Fondo {asset_id}", asset_type, asset_class, transferable, D(pnl))


def _dca(
    amount: str,
    *allocations: tuple[str, AssetClass, str],
    price_then: str | None = None,
    price_now: str | None = None,
) -> DcaIn:
    lines = tuple(
        AllocationIn(
            asset_id=asset_id,
            name=f"Fondo {asset_id}",
            asset_class=asset_class,
            weight=D(weight),
            price_now=D(price_now) if price_now else None,
            price_at_last=D(price_then) if price_then else None,
        )
        for asset_id, asset_class, weight in allocations
    )
    return DcaIn("dca_1", D(amount), lines)


def _input(**overrides: object) -> RadarInput:
    base: dict[str, object] = {
        "portfolio_id": "p1",
        "total_eur": TOTAL,
        "companies": (),
        "currencies": {"EUR": D("1")},
        "equity_weight": D("0.70"),
        "equity_target": D("0.70"),
        "drift_threshold": D("0.10"),
        "positions": (),
        "dca_plans": (),
    }
    base.update(overrides)
    return RadarInput(**base)  # type: ignore[arg-type]


def _only(findings: list[Finding], rule: RadarRule) -> Finding:
    found = [f for f in findings if f.rule is rule]
    assert len(found) == 1, findings
    return found[0]


def _rules(findings: list[Finding]) -> list[RadarRule]:
    return [f.rule for f in findings]


# --- Concentración: una empresa > 5 % O las 10 mayores > 25 % ---


def test_single_company_over_five_percent_fires() -> None:
    found = radar.evaluate(_input(companies=_companies("0.065", "0.03")))
    item = _only(found, RadarRule.CONCENTRATION)
    assert item.kind is RadarKind.RISK
    assert item.weight == D("0.065")
    assert item.value_eur == D("6500.00")
    assert item.user_rule is None
    assert item.facts["top_name"] == "Empresa 0"


def test_top_ten_over_25_percent_fires_without_single_company() -> None:
    # 11 empresas de 2,6 %: ninguna pasa del 5 %, las 10 mayores suman 26 %.
    found = radar.evaluate(_input(companies=_companies(*["0.026"] * 11)))
    item = _only(found, RadarRule.CONCENTRATION)
    assert item.weight == D("0.260")
    assert item.facts["single_fired"] is False
    assert item.facts["top10_fired"] is True


def test_concentration_limits_are_strict() -> None:
    # Justo 5 % y 10 × 2,5 % = 25 %: no saltan.
    assert radar.evaluate(_input(companies=_companies("0.05", *["0.0222"] * 9))) == []
    assert radar.evaluate(_input(companies=_companies(*["0.025"] * 10))) == []


def test_both_concentration_conditions_make_one_item() -> None:
    found = radar.evaluate(_input(companies=_companies("0.065", *["0.03"] * 9)))
    item = _only(found, RadarRule.CONCENTRATION)  # un solo item aunque saltan las dos
    assert item.facts["single_fired"] is True
    assert item.facts["top10_fired"] is True
    assert item.weight == D("0.065")


def test_residual_keys_are_not_companies() -> None:
    residual = (
        CompanyWeight("OTROS_FONDO", "Otros", D("0.40")),
        CompanyWeight("GOV_ES", "Deuda", D("0.30")),
        CompanyWeight("BONOS_X", "Bonos", D("0.20")),
    )
    assert radar.evaluate(_input(companies=residual)) == []


# --- Divisa: exposición no EUR > 50 %, sin contar la divisa desconocida ---


def test_currency_over_half_fires_with_main_currency() -> None:
    currencies = {"EUR": D("0.30"), "USD": D("0.55"), "JPY": D("0.05"), "OTHER": D("0.10")}
    item = _only(radar.evaluate(_input(currencies=currencies)), RadarRule.CURRENCY)
    assert item.kind is RadarKind.RISK
    assert item.weight == D("0.60")  # USD + JPY; "OTHER" (desconocida) no cuenta
    assert item.value_eur == D("60000.00")
    assert item.facts["top_currency"] == "USD"
    assert item.facts["top_currency_weight"] == D("0.55")


def test_currency_unknown_does_not_push_over_the_limit() -> None:
    currencies = {"EUR": D("0.45"), "USD": D("0.50"), "OTHER": D("0.05")}
    assert radar.evaluate(_input(currencies=currencies)) == []


# --- Desviación: |renta variable − objetivo| > umbral (fracción, estricto) ---


def test_drift_inside_threshold_does_not_fire() -> None:
    # Laura: 76 % frente a 70 %.
    assert radar.evaluate(_input(equity_weight=D("0.76"))) == []
    assert radar.evaluate(_input(equity_weight=D("0.80"))) == []  # justo 0,10: no salta


def test_drift_over_and_under_fire_with_sign() -> None:
    over = _only(radar.evaluate(_input(equity_weight=D("0.82"))), RadarRule.DRIFT)
    assert over.kind is RadarKind.RISK
    assert over.weight == D("0.12")
    assert over.value_eur == D("12000.00")
    under = _only(radar.evaluate(_input(equity_weight=D("0.55"))), RadarRule.DRIFT)
    assert under.weight == D("-0.15")
    assert under.value_eur == D("15000.00")


# --- Reequilibrio con aportaciones ---


def test_rebalance_months_when_dca_goes_to_the_underweight_class() -> None:
    # E = 82.000, objetivo 70 %: sobran E − t·T = 12.000.
    # Aportación 500/mes toda a renta fija: n = 12.000 / (0,70 · 500 − 0) = 34,3 → 35 meses.
    dca = _dca("500", ("IE_FI", AssetClass.FIXED_INCOME, "1"))
    found = radar.evaluate(_input(equity_weight=D("0.82"), dca_plans=(dca,)))
    item = _only(found, RadarRule.REBALANCE_WITH_DCA)
    assert item.kind is RadarKind.OPPORTUNITY
    assert item.facts["months"] == 35
    assert item.facts["monthly_eur"] == D("500")
    assert item.value_eur == D("12000.00")
    assert item.user_rule is not None
    assert (item.user_rule.source, item.user_rule.ref) == ("dca_plan", "dca_1")


def test_rebalance_counts_the_part_of_the_dca_that_goes_the_wrong_way() -> None:
    # 40 % a renta variable (200) y 60 % a renta fija: n = 12.000 / (0,70 · 500 − 200) = 80.
    dca = _dca("500", ("EQ", AssetClass.EQUITY, "0.4"), ("FI", AssetClass.FIXED_INCOME, "0.6"))
    item = _only(
        radar.evaluate(_input(equity_weight=D("0.82"), dca_plans=(dca,))),
        RadarRule.REBALANCE_WITH_DCA,
    )
    assert item.facts["months"] == 80


def test_rebalance_when_equity_is_underweight() -> None:
    # E = 55.000: faltan 15.000 (t·T − E = 70.000 − 55.000). Aportación 400/mes toda a renta
    # variable: n = 15.000 / (400 − 0,70 · 400) = 125 meses.
    dca = _dca("400", ("EQ", AssetClass.EQUITY, "1"))
    item = _only(
        radar.evaluate(_input(equity_weight=D("0.55"), dca_plans=(dca,))),
        RadarRule.REBALANCE_WITH_DCA,
    )
    assert item.facts["months"] == 125


def test_rebalance_needs_a_dca_that_helps() -> None:
    # Laura con objetivo 55 %: su DCA (70 % a renta variable) empuja hacia el lado equivocado.
    dca = _dca("300", ("EQ", AssetClass.EQUITY, "0.7"), ("FI", AssetClass.FIXED_INCOME, "0.3"))
    found = radar.evaluate(
        _input(equity_weight=D("0.76"), equity_target=D("0.55"), dca_plans=(dca,))
    )
    assert RadarRule.REBALANCE_WITH_DCA not in _rules(found)
    assert RadarRule.DRIFT in _rules(found)


def test_rebalance_needs_drift_and_dca() -> None:
    dca = _dca("500", ("FI", AssetClass.FIXED_INCOME, "1"))
    assert radar.evaluate(_input(equity_weight=D("0.76"), dca_plans=(dca,))) == []
    assert RadarRule.REBALANCE_WITH_DCA not in _rules(
        radar.evaluate(_input(equity_weight=D("0.82")))
    )


# --- Aportación más barata: el precio actual cae > 3 % desde la última aportación ---


def test_cheaper_contribution_fires_over_three_percent() -> None:
    dca = _dca("300", ("FUND", AssetClass.EQUITY, "0.7"), price_then="100", price_now="96")
    item = _only(radar.evaluate(_input(dca_plans=(dca,))), RadarRule.CHEAPER_CONTRIBUTION)
    assert item.kind is RadarKind.OPPORTUNITY
    assert item.weight == D("-0.04")
    assert item.value_eur == D("210.00")  # 300 € · 70 %
    assert item.ref == "FUND"
    assert item.user_rule is not None
    assert (item.user_rule.source, item.user_rule.ref) == ("dca_plan", "dca_1")


def test_cheaper_contribution_is_strict_and_ignores_rises_and_missing_prices() -> None:
    at_limit = _dca("300", ("FUND", AssetClass.EQUITY, "1"), price_then="100", price_now="97")
    rise = _dca("300", ("FUND", AssetClass.EQUITY, "1"), price_then="100", price_now="105")
    missing = _dca("300", ("FUND", AssetClass.EQUITY, "1"))
    for dca in (at_limit, rise, missing):
        assert radar.evaluate(_input(dca_plans=(dca,))) == []


# --- Traspaso sin tributar: solo con desviación y con regla del usuario (el plan) ---


def test_tax_free_transfer_from_overweight_to_underweight_class() -> None:
    positions = (
        _fund("EQ_A", AssetClass.EQUITY, "5000"),
        _fund("EQ_B", AssetClass.EQUITY, "2500"),
        _fund("FI_A", AssetClass.FIXED_INCOME, "300"),
    )
    found = radar.evaluate(_input(equity_weight=D("0.82"), positions=positions))
    item = _only(found, RadarRule.TAX_FREE_TRANSFER)
    assert item.kind is RadarKind.OPPORTUNITY
    assert item.value_eur == D("7500.00")  # plusvalía latente de los fondos de origen
    assert item.weight == D("0.12")
    assert item.user_rule is not None
    assert (item.user_rule.source, item.user_rule.ref) == ("plan", "p1")
    assert item.facts["origin_names"] == ("Fondo EQ_A", "Fondo EQ_B")
    assert item.facts["destination_names"] == ("Fondo FI_A",)


def test_tax_free_transfer_goes_to_equity_when_equity_is_underweight() -> None:
    positions = (_fund("FI_A", AssetClass.FIXED_INCOME, "800"), _fund("EQ_A", AssetClass.EQUITY))
    item = _only(
        radar.evaluate(_input(equity_weight=D("0.55"), positions=positions)),
        RadarRule.TAX_FREE_TRANSFER,
    )
    assert item.facts["origin_names"] == ("Fondo FI_A",)
    assert item.facts["destination_names"] == ("Fondo EQ_A",)


def test_tax_free_transfer_never_fires_without_drift() -> None:
    positions = (_fund("EQ_A", AssetClass.EQUITY, "5000"), _fund("FI_A", AssetClass.FIXED_INCOME))
    assert radar.evaluate(_input(equity_weight=D("0.76"), positions=positions)) == []


def test_tax_free_transfer_needs_gain_transferable_origin_and_destination() -> None:
    drift = {"equity_weight": D("0.82")}
    no_gain = (_fund("EQ_A", AssetClass.EQUITY, "0"), _fund("FI_A", AssetClass.FIXED_INCOME))
    loss = (_fund("EQ_A", AssetClass.EQUITY, "-100"), _fund("FI_A", AssetClass.FIXED_INCOME))
    etf = (
        _fund("EQ_A", AssetClass.EQUITY, "900", transferable=False, asset_type=AssetType.ETF),
        _fund("FI_A", AssetClass.FIXED_INCOME),
    )
    no_destination = (_fund("EQ_A", AssetClass.EQUITY, "900"),)
    for positions in (no_gain, loss, etf, no_destination):
        found = radar.evaluate(_input(positions=positions, **drift))
        assert RadarRule.TAX_FREE_TRANSFER not in _rules(found)


# --- Invariante y orden ---


def test_every_opportunity_has_a_user_rule() -> None:
    dca = _dca(
        "500",
        ("FI", AssetClass.FIXED_INCOME, "1"),
        price_then="100",
        price_now="90",
    )
    positions = (_fund("EQ_A", AssetClass.EQUITY, "5000"), _fund("FI_A", AssetClass.FIXED_INCOME))
    found = radar.evaluate(
        _input(
            equity_weight=D("0.82"),
            companies=_companies("0.07"),
            currencies={"EUR": D("0.2"), "USD": D("0.8")},
            positions=positions,
            dca_plans=(dca,),
        )
    )
    assert set(_rules(found)) == set(RadarRule)
    for item in found:
        if item.kind is RadarKind.OPPORTUNITY:
            assert item.user_rule is not None


def test_risks_come_before_opportunities_in_rule_order() -> None:
    dca = _dca("500", ("FI", AssetClass.FIXED_INCOME, "1"), price_then="100", price_now="90")
    positions = (_fund("EQ_A", AssetClass.EQUITY, "5000"), _fund("FI_A", AssetClass.FIXED_INCOME))
    found = radar.evaluate(
        _input(
            equity_weight=D("0.82"),
            companies=_companies("0.07"),
            currencies={"EUR": D("0.2"), "USD": D("0.8")},
            positions=positions,
            dca_plans=(dca,),
        )
    )
    assert _rules(found) == [
        RadarRule.CONCENTRATION,
        RadarRule.CURRENCY,
        RadarRule.DRIFT,
        RadarRule.REBALANCE_WITH_DCA,
        RadarRule.CHEAPER_CONTRIBUTION,
        RadarRule.TAX_FREE_TRANSFER,
    ]


def test_empty_portfolio_has_no_findings() -> None:
    assert radar.evaluate(_input(total_eur=D("0"))) == []
