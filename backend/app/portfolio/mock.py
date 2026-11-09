"""Mock del gestor de cartera: sirve los ejemplos de `schemas/examples/` (D-018).

Solo lectura y sin BD. Lo sustituyen T1-03 a T1-07: todas las rutas son reales (el traspaso desde
T1-05). Se borra en T2-03.
"""

from app.core.errors import AppError, ErrorCode
from app.schemas import examples
from app.schemas.portfolio import PortfolioOut, PortfolioSummaryOut

_PORTFOLIO_EXAMPLES = {"laura": "PortfolioOut", "javier": "PortfolioOut.javier"}


def _not_found(portfolio_id: str) -> AppError:
    return AppError(
        ErrorCode.NOT_FOUND,
        f"No existe la cartera «{portfolio_id}».",
        details={"portfolio_id": portfolio_id},
    )


def list_portfolio_ids() -> list[str]:
    return list(_PORTFOLIO_EXAMPLES)


def list_portfolios() -> list[PortfolioSummaryOut]:
    out = []
    for pid in list_portfolio_ids():
        p = get_valued(pid)
        out.append(PortfolioSummaryOut(id=p.id, name=p.name, profile=p.profile))
    return out


def get_valued(portfolio_id: str) -> PortfolioOut:
    name = _PORTFOLIO_EXAMPLES.get(portfolio_id)
    if name is None:
        raise _not_found(portfolio_id)
    return PortfolioOut.model_validate(examples.load(name))
