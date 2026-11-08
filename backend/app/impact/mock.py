"""Mock de la atribución de movimientos: sirve el ejemplo de `schemas/examples/` (D-018).

Sin BD ni cálculo. Lo sustituye T2-07; se borra en T2-03.
"""

from app.portfolio import service as portfolio_service
from app.schemas import examples
from app.schemas.impact import MoveAttributionOut, MovePeriod


def explain_move(portfolio_id: str, period: MovePeriod) -> MoveAttributionOut:
    portfolio_service.ensure_exists(portfolio_id)  # 404 si no existe
    move = MoveAttributionOut.model_validate(examples.load("MoveAttributionOut"))
    return move.model_copy(update={"period": period})
