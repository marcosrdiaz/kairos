"""Interfaz pública del gestor de cartera (diseño del MVP §4.1).

Otros módulos importan solo las cinco primeras funciones. El resto las usa `api/portfolio.py`.
De momento todo delega en `mock.py`; T1-03 a T1-07 cambian cada función a la implementación real
sin cambiar su firma.
"""

from datetime import datetime

from app.portfolio import mock
from app.schemas.portfolio import (
    AssetOut,
    DcaExecutionActionRequest,
    DcaExecutionOut,
    DcaExecutionStatus,
    DcaPlanCreateRequest,
    DcaPlanOut,
    DcaPlanUpdateRequest,
    PlanOut,
    PlanUpdateRequest,
    PortfolioOut,
    PortfolioSummaryOut,
    PositionsInitRequest,
    TransactionOut,
    TransactionRequest,
    TransferRequest,
    ValueChangeOut,
)

# --- Interfaz entre módulos (§4.1) ---


def get_valued(portfolio_id: str) -> PortfolioOut:
    return mock.get_valued(portfolio_id)


def get_plan(portfolio_id: str) -> PlanOut:
    return mock.get_plan(portfolio_id)


def list_dca_plans(portfolio_id: str) -> list[DcaPlanOut]:
    return mock.list_dca_plans(portfolio_id)


def get_value_change(portfolio_id: str, start: datetime, end: datetime) -> ValueChangeOut:
    return mock.get_value_change(portfolio_id, start, end)


def list_portfolio_ids() -> list[str]:
    return mock.list_portfolio_ids()


# --- Para la API de cartera ---


def list_portfolios() -> list[PortfolioSummaryOut]:
    return mock.list_portfolios()


def lookup_assets(query: str) -> list[AssetOut]:
    """Autocompletar del alta (`GET /assets/lookup?q=`): por ISIN, ticker o nombre."""
    return mock.lookup_assets(query)


def reset_demo() -> list[str]:
    """Devuelve Laura y Javier a su estado inicial (`/demo/reset`). Devuelve los IDs recargados."""
    return mock.list_portfolio_ids()


def init_positions(portfolio_id: str, request: PositionsInitRequest) -> PortfolioOut:
    return mock.get_valued(portfolio_id)


def register_transaction(portfolio_id: str, request: TransactionRequest) -> TransactionOut:
    return mock.register_transaction(portfolio_id)


def register_transfer(portfolio_id: str, request: TransferRequest) -> TransactionOut:
    return mock.register_transfer(portfolio_id, request)


def update_plan(portfolio_id: str, request: PlanUpdateRequest) -> PlanOut:
    plan = mock.get_plan(portfolio_id)
    return plan.model_copy(update=request.model_dump(exclude_unset=True))


def create_dca_plan(portfolio_id: str, request: DcaPlanCreateRequest) -> DcaPlanOut:
    plan = mock.list_dca_plans(portfolio_id)[0]
    return plan.model_copy(update=request.model_dump(exclude_unset=True))


def update_dca_plan(portfolio_id: str, plan_id: str, request: DcaPlanUpdateRequest) -> DcaPlanOut:
    plan = mock.list_dca_plans(portfolio_id)[0]
    return plan.model_copy(update={"id": plan_id, **request.model_dump(exclude_unset=True)})


def act_on_dca_execution(execution_id: str, request: DcaExecutionActionRequest) -> DcaExecutionOut:
    status = (
        DcaExecutionStatus.CONFIRMED if request.action == "confirm" else DcaExecutionStatus.SKIPPED
    )
    return mock.get_dca_execution(execution_id).model_copy(update={"status": status})
