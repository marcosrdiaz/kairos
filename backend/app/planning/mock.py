"""Mock de proyección y agenda: sirve los ejemplos de `schemas/examples/` (D-018).

Sin BD ni cálculo. Lo sustituyen T1-14 y T2-06; se borra en T2-03.
"""

from app.portfolio import service as portfolio_service
from app.schemas import examples
from app.schemas.planning import AgendaItemOut, ProjectionOut

_AGENDA_EXAMPLES = ("AgendaItemOut", "AgendaItemOut.dca")


def get_projection(portfolio_id: str) -> ProjectionOut:
    portfolio_service.ensure_exists(portfolio_id)  # 404 si no existe
    return ProjectionOut.model_validate(examples.load("ProjectionOut"))


def get_agenda(portfolio_id: str) -> list[AgendaItemOut]:
    portfolio_service.ensure_exists(portfolio_id)  # 404 si no existe
    return [AgendaItemOut.model_validate(examples.load(name)) for name in _AGENDA_EXAMPLES]
