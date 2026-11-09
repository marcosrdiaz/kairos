"""Mock del gestor de cartera: sirve los ejemplos de `schemas/examples/` (D-018).

Solo lectura y sin BD. Las escrituras devuelven el ejemplo de respuesta sin cambiar nada.
Lo sustituyen T1-03 a T1-07 (DCA real desde T1-06; plan y variación de valor desde T1-07); solo
queda el traspaso (T1-05). Se borra en T2-03.
"""

from app.core.errors import AppError, ErrorCode
from app.schemas import examples
from app.schemas.common import AssetType, ErrorOut
from app.schemas.portfolio import (
    PortfolioOut,
    PortfolioSummaryOut,
    TransactionOut,
    TransferRequest,
)

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


def register_transfer(portfolio_id: str, request: TransferRequest) -> TransactionOut:
    """Si alguno de los dos activos de la cartera no es fondo, 422 `TRANSFER_NOT_ALLOWED`."""
    portfolio = get_valued(portfolio_id)
    types = {p.asset_id: p.asset_type for p in portfolio.positions}
    involved = (types.get(request.from_asset_id), types.get(request.to_asset_id))
    if any(t is not None and t is not AssetType.FUND for t in involved):
        error = ErrorOut.model_validate(examples.load("ErrorOut.transfer_not_allowed"))
        details = {**error.details, "from_asset_type": involved[0], "to_asset_type": involved[1]}
        raise AppError(ErrorCode.TRANSFER_NOT_ALLOWED, error.message, details=details)
    return TransactionOut.model_validate(examples.load("TransactionOut.transfer"))
