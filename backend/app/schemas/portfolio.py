"""Contratos del gestor de cartera (diseño del MVP §4.1).

Ejemplos en `schemas/examples/<Modelo>.json` (y variantes `<Modelo>.<variante>.json`).
Convenciones de importes, participaciones, fracciones y fechas: `schemas/common.py`.
"""

from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Any, Literal, Self

from pydantic import Field, PlainSerializer, WithJsonSchema, model_validator

from app.schemas.common import (
    AssetClass,
    AssetType,
    ContractModel,
    Fraction,
    Money,
    PortfolioKind,
    Price,
    PriceKind,
    Profile,
    RiskProfile,
    SourceRef,
    TraceKind,
    Units,
    UtcDatetime,
)

FxRate = Annotated[
    Decimal,
    PlainSerializer(lambda v: format(v, "f"), return_type=str),
    WithJsonSchema(
        {
            "type": "string",
            "pattern": r"^\d+(\.\d+)?$",
            "description": "Tipo de cambio de la divisa del precio a EUR: 1 USD = 0.8621 EUR",
        }
    ),
]
"""Tipo de cambio `price_currency → EUR`. `"1"` si el precio ya está en euros."""

CalcId = Annotated[str, Field(pattern=r"^calc_")]
"""`"calc_"` + uuid4 hex (`core.trace.new_calc_id()`)."""


# --- Enums del módulo ---


class Frequency(StrEnum):
    MONTHLY = "monthly"
    WEEKLY = "weekly"


class DcaPlanStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"


class DcaExecutionStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SKIPPED = "skipped"


class OperationType(StrEnum):
    """Tipo en la respuesta. En BD hay además `transfer_out`, `transfer_in` e `initial`."""

    BUY = "buy"
    SELL = "sell"
    TRANSFER = "transfer"
    DCA_BUY = "dca_buy"


# --- Cartera valorada ---


class AllocationOut(ContractModel):
    equity: Fraction
    fixed_income: Fraction
    cash: Fraction
    mixed: Fraction


class PositionOut(ContractModel):
    asset_id: str
    isin: str | None
    ticker: str | None
    name: str
    asset_type: AssetType
    asset_class: AssetClass
    units: Units
    avg_cost_eur: Money
    price: Price
    price_currency: str
    price_at: UtcDatetime
    price_kind: PriceKind
    fx_rate: FxRate
    value_eur: Money
    weight: Fraction
    unrealized_pnl_eur: Money
    transferable: bool
    first_acquired_at: UtcDatetime


class DemoAdjustmentOut(ContractModel):
    """Ajuste de demo tras un replay (D-031). Ya está sumado en los totales."""

    event_id: str
    impact_eur: Money
    label: str
    calc_id: CalcId


class PortfolioOut(ContractModel):
    """`GET /portfolios/{id}`. `total_eur`, `change_week_*` y `value_eur` incluyen los ajustes.

    `profile` está obsoleto: usa `risk_profile` (T4-09). `kind` y `risk_profile` son `null` en
    las carteras creadas antes de T4-10.
    """

    id: str
    name: str
    profile: Profile
    kind: PortfolioKind | None = None
    risk_profile: RiskProfile | None = None
    total_eur: Money
    change_week_eur: Money
    change_week_pct: Fraction
    allocation: AllocationOut
    positions: list[PositionOut]
    demo_adjustments: list[DemoAdjustmentOut] = Field(default_factory=list)
    valued_at: UtcDatetime
    calc_id: CalcId


class PortfolioSummaryOut(ContractModel):
    """Elemento de `GET /portfolios` (selector de carteras). `profile` está obsoleto: usa
    `risk_profile` (T4-09)."""

    id: str
    name: str
    profile: Profile
    kind: PortfolioKind | None = None
    risk_profile: RiskProfile | None = None


class AssetOut(ContractModel):
    """Activo del catálogo: `GET /assets/lookup?q=` (lista). Completa el alta (RF-01).

    `id` es el ISIN; sin ISIN, un código propio (`DEP-12M`, `PP-MIXTO`). `ter` es `null` en
    acciones, depósitos y planes. La fuente del precio es interna y no sale en el contrato.
    """

    id: str
    isin: str | None
    ticker: str | None
    name: str
    asset_type: AssetType
    asset_class: AssetClass
    currency: str
    ter: Fraction | None
    transferable: bool
    price_kind: PriceKind


class AssetCreateRequest(ContractModel):
    """Alta de un activo que no está en el catálogo (`POST /assets`, T4-07): se busca en el
    proveedor de precios en directo por ISIN, ticker o nombre y se da de alta el primero que tenga
    precios. Si ya está en el catálogo, se devuelve ese."""

    query: str = Field(min_length=1, max_length=80)


class PositionInitLine(ContractModel):
    asset_id: str
    units: Units = Field(gt=0)
    avg_cost_eur: Money = Field(ge=0)
    acquired_at: UtcDatetime | None = None
    """Por defecto, `clock.now()`."""


class PositionsInitRequest(ContractModel):
    """`POST /portfolios/{id}/positions`: alta (tipo `initial`). Responde `PortfolioOut`."""

    positions: list[PositionInitLine] = Field(min_length=1)


# --- Plan ---


class TargetAllocation(ContractModel):
    equity: Fraction
    fixed_income: Fraction
    cash: Fraction


class PlanUpdateRequest(ContractModel):
    """`PUT /portfolios/{id}/plan`. Responde `PlanOut`."""

    target: TargetAllocation
    drift_threshold: Fraction = Decimal("0.10")
    goal_amount_eur: Money | None = None
    goal_year: int | None = None


class PlanOut(ContractModel):
    portfolio_id: str
    target: TargetAllocation
    drift_threshold: Fraction
    goal_amount_eur: Money | None
    goal_year: int | None
    current: TargetAllocation
    drift_equity: Fraction
    drift_exceeded: bool
    calc_id: CalcId


# --- Operaciones y traspasos ---


class _AmountOrUnits(ContractModel):
    amount_eur: Money | None = Field(default=None, gt=0)
    units: Units | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _exactly_one(self) -> Self:
        if (self.amount_eur is None) == (self.units is None):
            raise ValueError("Indica exactamente uno de `amount_eur` o `units`")
        return self


class TransactionRequest(_AmountOrUnits):
    """`POST /portfolios/{id}/transactions`. Compra o venta por importe o por participaciones."""

    type: Literal["buy", "sell"]
    asset_id: str


class TransferRequest(_AmountOrUnits):
    """`POST /portfolios/{id}/transfers`. Solo fondo → fondo; si no, 422 `TRANSFER_NOT_ALLOWED`."""

    from_asset_id: str
    to_asset_id: str


class LotOut(ContractModel):
    lot_id: str
    acquired_at: UtcDatetime
    units: Units
    cost_eur_per_unit: Money


class OperationEffect(ContractModel):
    """Efecto sobre el activo de origen. En un traspaso, `lots_created` son los del destino."""

    units_after: Units
    avg_cost_eur_after: Money
    realized_gain_eur: Money | None = None
    lots_consumed: list[LotOut] = Field(default_factory=list)
    lots_created: list[LotOut] = Field(default_factory=list)


class TransactionOut(ContractModel):
    """Respuesta 201 de una operación o un traspaso."""

    transaction_id: str
    type: OperationType
    asset_id: str
    to_asset_id: str | None = None
    """Solo en traspasos: fondo de destino."""
    units: Units
    price: Price
    price_currency: str
    price_at: UtcDatetime
    fx_rate: FxRate
    amount_eur: Money
    effect: OperationEffect
    portfolio: PortfolioOut
    calc_id: CalcId


# --- DCA ---


class DcaAllocation(ContractModel):
    asset_id: str
    weight: Fraction


class DcaPlanCreateRequest(ContractModel):
    """`POST /portfolios/{id}/dca-plans`. Σ weight = 1 exacto (si no, `DCA_ALLOCATION_INVALID`).

    `day`: día del mes (1-28) si es mensual; día ISO de la semana (1 = lunes) si es semanal.
    """

    amount_eur: Money = Field(gt=0)
    frequency: Frequency
    day: int = Field(ge=1, le=28)
    allocations: list[DcaAllocation] = Field(min_length=1)
    status: DcaPlanStatus = DcaPlanStatus.ACTIVE


class DcaPlanUpdateRequest(ContractModel):
    """`PATCH /portfolios/{id}/dca-plans/{plan_id}`. Solo los campos enviados."""

    amount_eur: Money | None = Field(default=None, gt=0)
    frequency: Frequency | None = None
    day: int | None = Field(default=None, ge=1, le=28)
    allocations: list[DcaAllocation] | None = Field(default=None, min_length=1)
    status: DcaPlanStatus | None = None


class DcaPlanOut(ContractModel):
    id: str
    portfolio_id: str
    amount_eur: Money
    frequency: Frequency
    day: int
    status: DcaPlanStatus
    allocations: list[DcaAllocation]
    last_execution_at: UtcDatetime | None
    next_execution_at: UtcDatetime | None


class DcaExecutionLine(ContractModel):
    asset_id: str
    amount_eur: Money
    price: Price
    price_at: UtcDatetime
    units_estimated: Units


class DcaExecutionOut(ContractModel):
    id: str
    dca_plan_id: str
    scheduled_for: UtcDatetime
    status: DcaExecutionStatus
    lines: list[DcaExecutionLine]


class DcaExecutionActionRequest(ContractModel):
    """`POST /dca-executions/{id}`. Responde `DcaExecutionOut`."""

    action: Literal["confirm", "skip"]


# --- Variación de valor (interno, para explain_move) ---


class AssetValueChange(ContractModel):
    asset_id: str
    start_value_eur: Money
    end_value_eur: Money
    flows_eur: Money


class ValueChangeOut(ContractModel):
    portfolio_id: str
    start: UtcDatetime
    end: UtcDatetime
    start_value_eur: Money
    end_value_eur: Money
    net_flows_eur: Money
    by_asset: list[AssetValueChange]
    calc_id: CalcId


# --- Traza ---


class TraceOut(ContractModel):
    """`GET /traces/{calc_id}` (endpoint en T2-01)."""

    calc_id: CalcId
    kind: TraceKind
    created_at: UtcDatetime
    formula: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    sources: list[SourceRef]
    parent_calc_ids: list[str] = Field(default_factory=list)
