"""Contrato del radar de riesgos y oportunidades (diseño del MVP §4.3).

Ejemplo en `schemas/examples/RadarOut.json`.
"""

from enum import StrEnum
from typing import Literal, Self

from pydantic import model_validator

from app.schemas.common import ContractModel, Fraction, Money


class RadarKind(StrEnum):
    RISK = "risk"
    OPPORTUNITY = "opportunity"


class RadarRule(StrEnum):
    CONCENTRATION = "concentration"
    CURRENCY = "currency"
    DRIFT = "drift"
    REBALANCE_WITH_DCA = "rebalance_with_dca"
    CHEAPER_CONTRIBUTION = "cheaper_contribution"
    TAX_FREE_TRANSFER = "tax_free_transfer"


class UserRule(ContractModel):
    """Regla del propio usuario frente a la que se expresa una oportunidad."""

    source: Literal["dca_plan", "plan"]
    ref: str


class RadarItem(ContractModel):
    """`title` y `detail` salen de plantillas deterministas, sin LLM."""

    id: str
    kind: RadarKind
    rule: RadarRule
    title: str
    detail: str
    value_eur: Money | None = None
    weight: Fraction | None = None
    user_rule: UserRule | None = None
    calc_id: str

    @model_validator(mode="after")
    def _opportunity_has_user_rule(self) -> Self:
        if self.kind is RadarKind.OPPORTUNITY and self.user_rule is None:
            raise ValueError("Una oportunidad necesita `user_rule`")
        return self


class RadarOut(ContractModel):
    """`GET /portfolios/{id}/radar`."""

    items: list[RadarItem]
    calc_id: str
