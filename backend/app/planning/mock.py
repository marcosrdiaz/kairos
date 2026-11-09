"""Mock de agenda: sirve los ejemplos de `schemas/examples/` (D-018).

Sin BD ni cálculo. Lo sustituye T2-06, que debe borrar este fichero.
"""

from app.portfolio import service as portfolio_service
from app.schemas import examples
from app.schemas.planning import AgendaItemOut

_AGENDA_EXAMPLES = ("AgendaItemOut", "AgendaItemOut.dca")


def get_agenda(portfolio_id: str) -> list[AgendaItemOut]:
    portfolio_service.ensure_exists(portfolio_id)  # 404 si no existe
    return [AgendaItemOut.model_validate(examples.load(name)) for name in _AGENDA_EXAMPLES]
