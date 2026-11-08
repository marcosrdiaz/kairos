"""Mock del estado del widget: sirve el ejemplo de `schemas/examples/` (D-018).

Sin BD ni cálculo. Lo sustituye T2-04; se borra en T2-03.
"""

from app.portfolio import service as portfolio_service
from app.schemas import examples
from app.schemas.status import StatusOut


def get_status(portfolio_id: str) -> StatusOut:
    portfolio_service.ensure_exists(portfolio_id)  # 404 si no existe
    return StatusOut.model_validate(examples.load("StatusOut"))
