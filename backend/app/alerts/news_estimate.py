"""Regla del aviso por noticia (`kind=news_estimate`, T4-31). Funciones puras.

Una noticia avisa si **el movimiento posible más grande** (el extremo de su rango más lejano de
cero, al alza o a la baja) supera el umbral de aviso de la cartera (D-032, D-094) multiplicado por
el factor de su perfil de riesgo. Avisa igual en los dos sentidos, también si el rango cruza el
cero («se puede mover entre −X y +Y»). Comparte el límite semanal por cartera con `event_impact`
y `market_move` (D-032, D-097).
"""

from decimal import Decimal

from app.alerts import config, engine

_LEGACY_PROFILE = {"dinamico": "agresivo"}  # `Profile` obsoleto (T4-09) → `RiskProfile`


def profile_factor(risk_profile: str | None, legacy_profile: str | None = None) -> Decimal:
    """Factor del umbral por perfil. Sin `risk_profile`, el `profile` obsoleto; sin ninguno, 1."""
    key = risk_profile or _LEGACY_PROFILE.get(legacy_profile or "", legacy_profile)
    return config.NEWS_PROFILE_FACTOR.get(key or "", Decimal("1"))


def largest_move(low_eur: Decimal, high_eur: Decimal) -> Decimal:
    """Tamaño (sin signo) del extremo del rango más lejano de cero."""
    return max(abs(low_eur), abs(high_eur))


def threshold_eur(total_eur: Decimal, factor: Decimal) -> Decimal:
    return engine.threshold_eur(total_eur) * factor


def score_if_alert(
    low_eur: Decimal, high_eur: Decimal, total_eur: Decimal, factor: Decimal
) -> Decimal | None:
    """Puntuación del aviso (`movimiento posible más grande / umbral del perfil`), o `None` si
    no hay que avisar."""
    score = largest_move(low_eur, high_eur) / threshold_eur(total_eur, factor)
    return score if score >= 1 else None
