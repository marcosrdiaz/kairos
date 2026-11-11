"""Regla del aviso por noticia (`kind=news_estimate`, T4-31). Funciones puras.

Una noticia avisa si **el extremo de su rango más cercano a cero** supera el umbral de aviso de
la cartera (D-032, D-094) multiplicado por el factor de su perfil de riesgo. Si el rango cruza el
cero, la noticia puede mover la cartera en los dos sentidos y no avisa. Comparte el límite semanal
por cartera con `event_impact` y `market_move` (D-032, D-097).
"""

from decimal import Decimal

from app.alerts import config, engine

_LEGACY_PROFILE = {"dinamico": "agresivo"}  # `Profile` obsoleto (T4-09) → `RiskProfile`


def profile_factor(risk_profile: str | None, legacy_profile: str | None = None) -> Decimal:
    """Factor del umbral por perfil. Sin `risk_profile`, el `profile` obsoleto; sin ninguno, 1."""
    key = risk_profile or _LEGACY_PROFILE.get(legacy_profile or "", legacy_profile)
    return config.NEWS_PROFILE_FACTOR.get(key or "", Decimal("1"))


def closest_to_zero(low_eur: Decimal, high_eur: Decimal) -> Decimal:
    """Extremo del rango más cercano a cero; 0 si el rango lo incluye."""
    if low_eur <= 0 <= high_eur:
        return Decimal("0")
    return low_eur if abs(low_eur) < abs(high_eur) else high_eur


def threshold_eur(total_eur: Decimal, factor: Decimal) -> Decimal:
    return engine.threshold_eur(total_eur) * factor


def score_if_alert(
    low_eur: Decimal, high_eur: Decimal, total_eur: Decimal, factor: Decimal
) -> Decimal | None:
    """Puntuación del aviso (`|extremo cercano a cero| / umbral del perfil`), o `None` si no hay
    que avisar."""
    nearest = closest_to_zero(low_eur, high_eur)
    score = abs(nearest) / threshold_eur(total_eur, factor)
    return score if nearest != 0 and score >= 1 else None
