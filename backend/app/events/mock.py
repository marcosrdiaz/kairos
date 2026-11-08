"""Mock de eventos: sirve el ejemplo de `ReplayOut` (D-018).

Lo sustituye T1-15; se borra en T2-03.
"""

from app.schemas import examples
from app.schemas.events import ReplayOut


def replay(event_id: str) -> ReplayOut:
    result = ReplayOut.model_validate(examples.load("ReplayOut"))
    return result.model_copy(update={"event_id": event_id})
