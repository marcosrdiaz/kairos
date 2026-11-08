"""Mock de avisos: sirve el ejemplo de `AlertOut` (D-018).

Lo sustituye T2-08; se borra en T2-03.
"""

from app.schemas import examples
from app.schemas.alerts import AlertOut


def list_alerts() -> list[AlertOut]:
    return [AlertOut.model_validate(examples.load("AlertOut"))]
