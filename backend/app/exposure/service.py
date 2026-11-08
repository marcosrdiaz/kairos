"""Interfaz pública de exposición y radar (diseño del MVP §4.2).

De momento delega en `mock.py`; T1-11 y T2-05 lo cambian sin cambiar las firmas.
"""

from collections.abc import Collection, Iterable
from decimal import Decimal

from app.exposure import mock
from app.schemas.exposure import ExposureOut
from app.schemas.radar import RadarOut


def company_weights(
    asset_ids: Iterable[str], companies: Collection[str]
) -> dict[str, dict[str, Decimal]]:
    """Peso de cada empresa en cada fondo o ETF: `{asset_id: {constituent_key: peso}}`.

    Solo incluye los pares con fila en la composición: sin fila, la empresa no está en el fondo.
    """
    return mock.company_weights(asset_ids, companies)


def get_exposure(portfolio_id: str) -> ExposureOut:
    return mock.get_exposure(portfolio_id)


def get_radar(portfolio_id: str) -> RadarOut:
    return mock.get_radar(portfolio_id)
