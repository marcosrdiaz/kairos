"""Contrato de exposición por look-through (diseño del MVP §4.3).

Ejemplo en `schemas/examples/ExposureOut.json`.
"""

from app.schemas.common import ContractModel, Fraction, Money, UtcDatetime


class ExposureBucket(ContractModel):
    key: str
    label: str
    value_eur: Money
    weight: Fraction


class CompanyHolding(ContractModel):
    """Activo de la cartera que contiene la empresa. Una acción directa pesa `"1"`."""

    asset_id: str
    weight_in_asset: Fraction


class TopCompany(ContractModel):
    key: str
    name: str
    value_eur: Money
    weight: Fraction
    held_in: list[CompanyHolding]


class OverlapItem(ContractModel):
    key: str
    name: str
    weight: Fraction
    asset_ids: list[str]


class TopCountry(ContractModel):
    key: str
    label: str
    weight: Fraction


class TopCompaniesGroup(ContractModel):
    n: int
    weight: Fraction


class Radiography(ContractModel):
    """Paso 2 del guion. `num_holdings` cuenta fondos y ETF."""

    num_holdings: int
    top_country: TopCountry
    top_companies_group: TopCompaniesGroup


class ExposureOut(ContractModel):
    """`GET /portfolios/{id}/exposure`."""

    by_country: list[ExposureBucket]
    by_sector: list[ExposureBucket]
    by_currency: list[ExposureBucket]
    top_companies: list[TopCompany]
    overlap: list[OverlapItem]
    radiography: Radiography
    coverage_pct: Fraction
    as_of: UtcDatetime
    calc_id: str
