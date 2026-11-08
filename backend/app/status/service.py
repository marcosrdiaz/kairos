"""Interfaz pública del estado del widget (diseño del MVP §4.2).

De momento delega en `mock.py`; T2-04 lo cambia sin cambiar las firmas.
"""

from app.schemas.status import StatusOut
from app.status import mock


def get_status(portfolio_id: str) -> StatusOut:
    return mock.get_status(portfolio_id)


def recompute(portfolio_id: str) -> StatusOut:
    return mock.get_status(portfolio_id)
