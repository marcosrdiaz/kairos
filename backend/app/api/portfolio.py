"""Endpoints de cartera, plan, operaciones, traspasos y DCA (diseño del MVP §4.1)."""

from typing import Any

from fastapi import APIRouter

from app.portfolio import service
from app.schemas.common import ErrorOut
from app.schemas.portfolio import (
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
)

router = APIRouter(tags=["portfolio"])

_NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"model": ErrorOut}}
_UNPROCESSABLE: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorOut},
    422: {"model": ErrorOut},
}


@router.get("/portfolios", response_model=list[PortfolioSummaryOut])
def list_portfolios() -> list[PortfolioSummaryOut]:
    return service.list_portfolios()


@router.get("/portfolios/{portfolio_id}", response_model=PortfolioOut, responses=_NOT_FOUND)
def get_portfolio(portfolio_id: str) -> PortfolioOut:
    return service.get_valued(portfolio_id)


@router.post(
    "/portfolios/{portfolio_id}/positions",
    response_model=PortfolioOut,
    status_code=201,
    responses=_UNPROCESSABLE,
)
def init_positions(portfolio_id: str, body: PositionsInitRequest) -> PortfolioOut:
    return service.init_positions(portfolio_id, body)


@router.post(
    "/portfolios/{portfolio_id}/transactions",
    response_model=TransactionOut,
    status_code=201,
    responses=_UNPROCESSABLE,
)
def register_transaction(portfolio_id: str, body: TransactionRequest) -> TransactionOut:
    return service.register_transaction(portfolio_id, body)


@router.post(
    "/portfolios/{portfolio_id}/transfers",
    response_model=TransactionOut,
    status_code=201,
    responses=_UNPROCESSABLE,
)
def register_transfer(portfolio_id: str, body: TransferRequest) -> TransactionOut:
    return service.register_transfer(portfolio_id, body)


@router.get("/portfolios/{portfolio_id}/plan", response_model=PlanOut, responses=_NOT_FOUND)
def get_plan(portfolio_id: str) -> PlanOut:
    return service.get_plan(portfolio_id)


@router.put("/portfolios/{portfolio_id}/plan", response_model=PlanOut, responses=_UNPROCESSABLE)
def update_plan(portfolio_id: str, body: PlanUpdateRequest) -> PlanOut:
    return service.update_plan(portfolio_id, body)


@router.get(
    "/portfolios/{portfolio_id}/dca-plans", response_model=list[DcaPlanOut], responses=_NOT_FOUND
)
def list_dca_plans(portfolio_id: str) -> list[DcaPlanOut]:
    return service.list_dca_plans(portfolio_id)


@router.post(
    "/portfolios/{portfolio_id}/dca-plans",
    response_model=DcaPlanOut,
    status_code=201,
    responses=_UNPROCESSABLE,
)
def create_dca_plan(portfolio_id: str, body: DcaPlanCreateRequest) -> DcaPlanOut:
    return service.create_dca_plan(portfolio_id, body)


@router.patch(
    "/portfolios/{portfolio_id}/dca-plans/{plan_id}",
    response_model=DcaPlanOut,
    responses=_UNPROCESSABLE,
)
def update_dca_plan(portfolio_id: str, plan_id: str, body: DcaPlanUpdateRequest) -> DcaPlanOut:
    return service.update_dca_plan(portfolio_id, plan_id, body)


@router.get(
    "/portfolios/{portfolio_id}/dca-executions",
    response_model=list[DcaExecutionOut],
    responses=_NOT_FOUND,
)
def list_dca_executions(
    portfolio_id: str, status: DcaExecutionStatus | None = None
) -> list[DcaExecutionOut]:
    """Aportaciones de la cartera, de la más reciente a la más antigua. `?status=pending` para
    las que esperan confirmar o saltar."""
    return service.list_dca_executions(portfolio_id, status)


@router.post(
    "/dca-executions/{execution_id}", response_model=DcaExecutionOut, responses=_UNPROCESSABLE
)
def act_on_dca_execution(execution_id: str, body: DcaExecutionActionRequest) -> DcaExecutionOut:
    """Confirmar (compra `dca_buy` al precio de ahora) o saltar una aportación pendiente. 422 si
    ya está resuelta."""
    return service.act_on_dca_execution(execution_id, body)
