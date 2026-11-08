"""Mock del radar: sirve el ejemplo de `schemas/examples/` (D-018).

Sin BD ni cálculo. Lo sustituye T2-05; se borra en T2-03.
"""

from app.portfolio import service as portfolio_service
from app.schemas import examples
from app.schemas.radar import RadarOut


def get_radar(portfolio_id: str) -> RadarOut:
    portfolio_service.ensure_exists(portfolio_id)  # 404 si no existe
    return RadarOut.model_validate(examples.load("RadarOut"))
