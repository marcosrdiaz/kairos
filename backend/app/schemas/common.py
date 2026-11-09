"""Tipos comunes de todos los contratos (diseño del MVP §3).

- Importes (`Money`): Decimal serializado como string con 2 decimales, "40123.45".
- Participaciones y precios (`Units`, `Price`): string con 8 decimales, "152.30451200".
- Pesos, porcentajes y variaciones (`Fraction`): fracción como string, "0.76" = 76 %.
- Fechas (`UtcDatetime`): ISO 8601 en UTC con `Z`.
"""

from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from enum import StrEnum
from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, ConfigDict, PlainSerializer, WithJsonSchema

_CENT = Decimal("0.01")
_UNIT = Decimal("0.00000001")


def _quantize(value: Decimal, step: Decimal) -> str:
    return format(value.quantize(step, rounding=ROUND_HALF_EVEN), "f")


def _decimal_string(description: str, pattern: str) -> WithJsonSchema:
    return WithJsonSchema({"type": "string", "pattern": pattern, "description": description})


Money = Annotated[
    Decimal,
    PlainSerializer(lambda v: _quantize(v, _CENT), return_type=str),
    _decimal_string("Importe en euros con 2 decimales", r"^-?\d+\.\d{2}$"),
]
"""Importe en EUR (salvo que el modelo indique `price_currency`)."""

Units = Annotated[
    Decimal,
    PlainSerializer(lambda v: _quantize(v, _UNIT), return_type=str),
    _decimal_string("Participaciones con 8 decimales", r"^-?\d+\.\d{8}$"),
]
"""Participaciones."""

Price = Annotated[
    Decimal,
    PlainSerializer(lambda v: _quantize(v, _UNIT), return_type=str),
    _decimal_string("Precio con 8 decimales", r"^-?\d+\.\d{8}$"),
]
"""Precio unitario en la divisa del activo."""

Fraction = Annotated[
    Decimal,
    PlainSerializer(lambda v: format(v, "f"), return_type=str),
    _decimal_string("Fracción: 0.76 = 76 %", r"^-?\d+(\.\d+)?$"),
]
"""Peso, porcentaje o variación como fracción. Nunca puntos porcentuales."""


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("La fecha necesita zona horaria")
    return value.astimezone(UTC)


UtcDatetime = Annotated[
    datetime,
    AfterValidator(_to_utc),
    PlainSerializer(
        lambda v: v.astimezone(UTC).isoformat().replace("+00:00", "Z"), return_type=str
    ),
    WithJsonSchema({"type": "string", "format": "date-time"}),
]
"""Fecha con zona horaria, serializada en UTC con `Z`."""


class ContractModel(BaseModel):
    """Base de los modelos de contrato: rechaza campos desconocidos.

    La marca `"illustrative": true` de los JSON de `schemas/examples/` no es parte del contrato:
    quien cargue un ejemplo (tests, `mock.py`) la quita antes de validar.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# --- Enums compartidos (en inglés y minúsculas; los textos visibles van en *_label) ---


class AssetType(StrEnum):
    FUND = "fund"
    ETF = "etf"
    STOCK = "stock"
    DEPOSIT = "deposit"
    PENSION_PLAN = "pension_plan"


class AssetClass(StrEnum):
    EQUITY = "equity"
    FIXED_INCOME = "fixed_income"
    CASH = "cash"
    MIXED = "mixed"


class PriceKind(StrEnum):
    INTRADAY = "intraday"
    NAV_DAILY = "nav_daily"


class Profile(StrEnum):
    CONSERVADOR = "conservador"
    MODERADO = "moderado"
    DINAMICO = "dinamico"


class Factor(StrEnum):
    EQ_GLOBAL = "EQ_GLOBAL"
    EQ_US_TECH = "EQ_US_TECH"
    RATES_EUR = "RATES_EUR"
    OIL = "OIL"
    EURUSD = "EURUSD"


class Confidence(StrEnum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class Polarity(StrEnum):
    RIESGO = "riesgo"
    OPORTUNIDAD = "oportunidad"
    NEUTRAL = "neutral"


class SourceKind(StrEnum):
    PRICE = "price"
    FX = "fx"
    COMPOSITION = "composition"
    BETA = "beta"
    EVENT = "event"
    ASSUMPTION = "assumption"
    USER_INPUT = "user_input"


class TraceKind(StrEnum):
    VALUATION = "valuation"
    TRANSACTION = "transaction"
    TRANSFER = "transfer"
    DCA = "dca"
    PLAN = "plan"
    EXPOSURE = "exposure"
    EVENT_IMPACT = "event_impact"
    SCENARIO = "scenario"
    PROJECTION = "projection"
    STATUS = "status"
    RADAR = "radar"
    MOVE = "move"
    AGENDA = "agenda"


# --- Modelos comunes ---


class SourceRef(ContractModel):
    """Fuente de una cifra. Ejemplo:
    {"kind": "price", "label": "VL iShares Core MSCI World", "ref": "IE00B4L5Y983",
     "as_of": "2026-11-06T00:00:00Z", "url": null}
    """

    kind: SourceKind
    label: str
    ref: str
    as_of: UtcDatetime | None = None
    url: str | None = None


class ErrorOut(ContractModel):
    """Cuerpo de toda respuesta de error HTTP 4xx/5xx. `code` es uno de `core.errors.ErrorCode`."""

    code: str
    message: str
    details: dict[str, Any] = {}
