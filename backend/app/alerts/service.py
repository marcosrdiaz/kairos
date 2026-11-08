"""Interfaz pública de `alerts` (diseño del MVP §4.4).

De momento delega en `mock.py`; T2-08 lo cambia por la lógica real sin cambiar la firma.
"""

from app.alerts import mock
from app.portfolio import service as portfolio_service
from app.schemas.alerts import AlertOut


def evaluate(portfolio_id: str, event_id: str) -> None:
    """Decide si un evento genera aviso. Aún no hace nada: lo implementa T2-08."""


def list_alerts(portfolio_id: str) -> list[AlertOut]:
    portfolio_service.ensure_exists(portfolio_id)  # NOT_FOUND si la cartera no existe
    return mock.list_alerts()
