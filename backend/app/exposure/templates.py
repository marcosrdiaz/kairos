"""Plantillas deterministas del radar: sin LLM, con las cifras del propio cálculo.

Español de España ("42.380 euros", "61 %"). Contexto, no órdenes (regla de producto 2): nunca
"compra", "vende" ni "te recomiendo". Un test pasa `forbidden.yaml` por todas las salidas.
"""

from collections.abc import Callable
from decimal import Decimal

from app.agents.fact_format import format_eur, format_fraction
from app.exposure.radar import Finding
from app.schemas.common import AssetClass
from app.schemas.radar import RadarRule

_CURRENCY_NAMES = {
    "USD": "el dólar",
    "JPY": "el yen",
    "GBP": "la libra",
    "CHF": "el franco suizo",
    "CAD": "el dólar canadiense",
    "AUD": "el dólar australiano",
}
_CLASS_NAMES = {AssetClass.EQUITY: "renta variable", AssetClass.FIXED_INCOME: "renta fija"}

Texts = tuple[str, str]


def _class_name(asset_class: AssetClass) -> str:
    return _CLASS_NAMES.get(asset_class, asset_class.value)


def _join(names: tuple[str, ...]) -> str:
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} y {names[-1]}"


def _eur(value: Decimal | None) -> str:
    return format_eur(value if value is not None else Decimal(0))


def _concentration(f: Finding) -> Texts:
    facts = f.facts
    if facts["single_fired"]:
        name = facts["top_name"]
        title = f"{name} pesa un {format_fraction(facts['top_weight'])} de tu cartera"
        detail = (
            f"Sumando lo que tienes directamente y lo que hay dentro de tus fondos y ETF, {name} "
            f"representa {_eur(f.value_eur)}. Si a esa empresa le va mal, tu cartera lo nota más "
            "que si el dinero estuviera repartido."
        )
        if facts["top10_fired"]:
            detail += f" Tus 10 mayores empresas suman un {format_fraction(facts['top10_weight'])}."
        return title, detail
    title = (
        f"Tus 10 mayores empresas suman un {format_fraction(facts['top10_weight'])} de la cartera"
    )
    detail = (
        f"Son unos {_eur(f.value_eur)} entre tus acciones y el interior de tus fondos. Aunque "
        "tengas varios fondos, buena parte del dinero depende de pocas empresas."
    )
    return title, detail


def _currency(f: Finding) -> Texts:
    code = f.facts["top_currency"]
    name = _CURRENCY_NAMES.get(code, code)
    share = format_fraction(f.weight or Decimal(0))
    title = f"El {share} de tu dinero está en divisas distintas del euro"
    main_share = format_fraction(f.facts["top_currency_weight"])
    detail = (
        f"La principal es {name} ({main_share}). Si esa divisa cae frente al euro, tu cartera "
        "pierde valor aunque la bolsa no se mueva."
    )
    return title, detail


def _drift(f: Finding) -> Texts:
    facts = f.facts
    side = "por encima" if facts["direction"] == "over" else "por debajo"
    title = (
        f"Tu renta variable pesa un {format_fraction(facts['equity'])} "
        f"y tu plan dice {format_fraction(facts['target'])}"
    )
    detail = (
        f"Estás {side} del objetivo de tu plan en un {format_fraction(f.weight or Decimal(0))}; "
        f"el umbral que has fijado es del {format_fraction(facts['threshold'])}."
    )
    return title, detail


def _rebalance(f: Finding) -> Texts:
    months = f.facts["months"]
    unit = "mes" if months == 1 else "meses"
    target = _class_name(f.facts["target_class"])
    title = f"Tus aportaciones pueden corregir la desviación en {months} {unit}"
    detail = (
        f"Con tu aportación de {_eur(f.facts['monthly_eur'])} al mes, la {target} iría ganando "
        "peso hasta el objetivo de tu plan. Ahora mismo la desviación equivale a "
        f"{_eur(f.value_eur)}."
    )
    return title, detail


def _cheaper(f: Finding) -> Texts:
    facts = f.facts
    title = "Tu aportación de este mes entra a un precio más bajo"
    detail = (
        f"{facts['asset_name']} cotiza un {format_fraction(facts['drop'])} por debajo de cuando se "
        "hizo tu última aportación. Tu plan destina "
        f"{_eur(facts['amount_eur'])} este mes a ese fondo."
    )
    return title, detail


def _tax_free(f: Finding) -> Texts:
    facts = f.facts
    origin = _class_name(facts["origin_class"])
    destination = _class_name(facts["destination_class"])
    title = "Un traspaso entre fondos acercaría tu cartera a tu plan sin tributar"
    detail = (
        f"Tus fondos traspasables de {origin} ({_join(facts['origin_names'])}) acumulan "
        f"{_eur(f.value_eur)} de plusvalía latente. Un traspaso a "
        f"{_join(facts['destination_names'])} no tributa hasta el momento de la venta, y tu plan "
        f"pide menos {origin} y más {destination}."
    )
    return title, detail


_RENDERERS: dict[RadarRule, Callable[[Finding], Texts]] = {
    RadarRule.CONCENTRATION: _concentration,
    RadarRule.CURRENCY: _currency,
    RadarRule.DRIFT: _drift,
    RadarRule.REBALANCE_WITH_DCA: _rebalance,
    RadarRule.CHEAPER_CONTRIBUTION: _cheaper,
    RadarRule.TAX_FREE_TRANSFER: _tax_free,
}


def render(finding: Finding) -> Texts:
    """`(title, detail)` del aviso."""
    return _RENDERERS[finding.rule](finding)
