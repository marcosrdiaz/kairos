"""Plantillas del radar (`exposure/templates.py`): deterministas, es-ES y sin órdenes.

Regla de producto 2: contexto, no órdenes. Ningún texto pasa por el LLM, pero todos pasan por
`forbidden.yaml`, y cada cifra sale del cálculo (nunca fija en la plantilla).
"""

from decimal import Decimal

import pytest

from app.agents import guardian
from app.exposure import radar, templates
from app.exposure.radar import AllocationIn, CompanyWeight, DcaIn, Finding, PositionIn, RadarInput
from app.schemas.common import AssetClass, AssetType
from app.schemas.radar import RadarRule

D = Decimal


def _everything(
    *,
    top: str = "0.07",
    usd: str = "0.80",
    equity: str = "0.82",
    price_now: str = "90",
    gain: str = "5000",
) -> list[Finding]:
    """Una cartera de laboratorio en la que saltan las 6 reglas."""
    allocation = AllocationIn(
        "FI", "Fondo de bonos", AssetClass.FIXED_INCOME, D("1"), D(price_now), D("100")
    )
    return radar.evaluate(
        RadarInput(
            portfolio_id="p1",
            total_eur=D("100000"),
            companies=(CompanyWeight("NVDA", "NVIDIA", D(top)),),
            currencies={"EUR": D("1") - D(usd), "USD": D(usd)},
            equity_weight=D(equity),
            equity_target=D("0.70"),
            drift_threshold=D("0.10"),
            positions=(
                PositionIn("EQ", "Fondo global", AssetType.FUND, AssetClass.EQUITY, True, D(gain)),
                PositionIn(
                    "FI", "Fondo de bonos", AssetType.FUND, AssetClass.FIXED_INCOME, True, D("0")
                ),
            ),
            dca_plans=(DcaIn("dca_1", D("500"), (allocation,)),),
        )
    )


def _texts(findings: list[Finding]) -> list[tuple[Finding, str, str]]:
    return [(f, *templates.render(f)) for f in findings]


def test_all_six_rules_are_covered() -> None:
    assert {f.rule for f in _everything()} == set(RadarRule)


def test_no_template_contains_forbidden_patterns() -> None:
    for finding, title, detail in _texts(_everything()):
        for text in (title, detail):
            assert guardian.find_forbidden(text) == [], (finding.rule, text)


def test_forbidden_patterns_hold_for_every_branch_of_each_template() -> None:
    variants = [
        _everything(top="0.03"),  # sin concentración: solo el resto de reglas
        _everything(top="0.20"),
        _everything(usd="0.60", equity="0.55"),  # renta variable infraponderada
        _everything(equity="0.55", price_now="80"),
    ]
    for findings in variants:
        for finding, title, detail in _texts(findings):
            assert guardian.find_forbidden(f"{title} {detail}") == [], (finding.rule, title)


def test_texts_are_spanish_formatted_and_use_the_calculation() -> None:
    texts = {f.rule: (title, detail) for f, title, detail in _texts(_everything())}
    concentration = texts[RadarRule.CONCENTRATION]
    assert "NVIDIA" in concentration[0]
    assert "7 %" in concentration[0]  # 0,07 → "7 %"
    assert "7.000 euros" in concentration[1]  # miles con punto, sin signo
    currency = texts[RadarRule.CURRENCY]
    assert "80 %" in currency[0]
    assert "USD" in currency[1] or "dólar" in currency[1]
    assert "12 %" in texts[RadarRule.DRIFT][1]
    assert "35 meses" in texts[RadarRule.REBALANCE_WITH_DCA][0]
    assert "10 %" in texts[RadarRule.CHEAPER_CONTRIBUTION][1]
    assert "5.000 euros" in texts[RadarRule.TAX_FREE_TRANSFER][1]


def test_figures_change_with_the_calculation() -> None:
    before = {f.rule: templates.render(f) for f in _everything(top="0.07")}
    after = {f.rule: templates.render(f) for f in _everything(top="0.09")}
    assert before[RadarRule.CONCENTRATION] != after[RadarRule.CONCENTRATION]
    assert "9 %" in after[RadarRule.CONCENTRATION][0]


def test_months_use_singular_and_plural() -> None:
    finding = next(f for f in _everything() if f.rule is RadarRule.REBALANCE_WITH_DCA)
    one = Finding(**{**finding.__dict__, "facts": {**finding.facts, "months": 1}})
    assert "1 mes " in templates.render(one)[0] + " "
    assert "meses" not in templates.render(one)[0]


@pytest.mark.parametrize("rule", list(RadarRule))
def test_every_text_is_plain_and_complete(rule: RadarRule) -> None:
    finding = next(f for f in _everything() if f.rule is rule)
    title, detail = templates.render(finding)
    for text in (title, detail):
        assert text.strip() == text and text
        assert "{" not in text and "}" not in text and "None" not in text
        assert "<" not in text  # ni marcadores ni HTML
    assert detail.endswith(".")
