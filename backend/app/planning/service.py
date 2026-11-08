"""Interfaz pública de proyección y agenda (diseño del MVP §4.2, D-029).

De momento delega en `mock.py`; T1-14 y T2-06 lo cambian sin cambiar las firmas.
"""

from app.planning import mock
from app.schemas.planning import AgendaItemOut, ProjectionOut


def get_projection(portfolio_id: str) -> ProjectionOut:
    return mock.get_projection(portfolio_id)


def get_agenda(portfolio_id: str) -> list[AgendaItemOut]:
    return mock.get_agenda(portfolio_id)
