"""Interfaz pública de `events`: control del replay (diseño del MVP §4.6).

De momento delega en `mock.py`; T1-15 lo cambia por el pipeline real sin cambiar la firma.
"""

from app.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.events import mock
from app.schemas.events import EventIn, ReplayOut


def get_event(event_id: str) -> EventIn:
    """Título, fecha y consenso de un evento, para el motor de impacto."""
    return mock.get_event(event_id)


def replay(event_id: str) -> ReplayOut:
    """Inyecta un evento del modo replay. Solo con `DEMO_MODE=true`."""
    if not get_settings().demo_mode:
        raise AppError(ErrorCode.DEMO_MODE_DISABLED, "El modo demo está desactivado.")
    return mock.replay(event_id)
