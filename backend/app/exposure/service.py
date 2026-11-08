"""Interfaz pública de exposición y radar (diseño del MVP §4.2).

De momento delega en `mock.py`; T1-11 y T2-05 lo cambian sin cambiar las firmas.
"""

from app.exposure import mock
from app.schemas.exposure import ExposureOut
from app.schemas.radar import RadarOut


def get_exposure(portfolio_id: str) -> ExposureOut:
    return mock.get_exposure(portfolio_id)


def get_radar(portfolio_id: str) -> RadarOut:
    return mock.get_radar(portfolio_id)
