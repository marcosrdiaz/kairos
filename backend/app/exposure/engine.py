"""Look-through de la cartera (`SPEC.md` §8.4): funciones puras, sin BD. Todo en `Decimal`.

Claves y residuos de las composiciones: D-049. Criterios de esta tarea: D-052.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

from app.schemas.common import AssetType
from app.schemas.exposure import (
    CompanyHolding,
    ExposureBucket,
    OverlapItem,
    Radiography,
    TopCompaniesGroup,
    TopCompany,
    TopCountry,
)

FORMULA = (
    "exposición_x = Σ_i V_i · Σ_c w_{i,c} · [c pertenece a x]; "
    "cobertura = parte del patrimonio con país conocido; "
    "solapamiento = empresas presentes en ≥ 2 posiciones"
)

UNKNOWN_COUNTRY = "OTHER"
UNKNOWN_CURRENCY = "OTHER"
UNKNOWN_SECTOR = "other"
TOP_COMPANIES_LIMIT = 20
TOP_COMPANIES_GROUP_N = 7

_ZERO = Decimal("0")
_WEIGHT_STEP = Decimal("0.0001")
_NON_COMPANY_PREFIXES = ("OTROS_", "GOV_", "BONOS_")
_FUND_TYPES = {AssetType.FUND, AssetType.ETF}
_OTHER_LABEL = "Otros"

_COUNTRY_LABELS: Mapping[str, str] = {
    "AE": "Emiratos Árabes Unidos",
    "AT": "Austria",
    "AU": "Australia",
    "BE": "Bélgica",
    "BM": "Bermudas",
    "BR": "Brasil",
    "CA": "Canadá",
    "CH": "Suiza",
    "CN": "China",
    "CY": "Chipre",
    "CZ": "Chequia",
    "DE": "Alemania",
    "DK": "Dinamarca",
    "EE": "Estonia",
    "ES": "España",
    "FI": "Finlandia",
    "FR": "Francia",
    "GB": "Reino Unido",
    "GR": "Grecia",
    "HK": "Hong Kong",
    "HR": "Croacia",
    "HU": "Hungría",
    "IE": "Irlanda",
    "IL": "Israel",
    "IN": "India",
    "IS": "Islandia",
    "IT": "Italia",
    "JP": "Japón",
    "KR": "Corea del Sur",
    "LT": "Lituania",
    "LU": "Luxemburgo",
    "LV": "Letonia",
    "MT": "Malta",
    "MX": "México",
    "NL": "Países Bajos",
    "NO": "Noruega",
    "NZ": "Nueva Zelanda",
    "PL": "Polonia",
    "PT": "Portugal",
    "RO": "Rumanía",
    "SA": "Arabia Saudí",
    "SE": "Suecia",
    "SG": "Singapur",
    "SI": "Eslovenia",
    "SK": "Eslovaquia",
    "TW": "Taiwán",
    "US": "Estados Unidos",
    "ZA": "Sudáfrica",
    UNKNOWN_COUNTRY: _OTHER_LABEL,
}
_SECTOR_LABELS: Mapping[str, str] = {
    "communication_services": "Comunicaciones",
    "consumer_discretionary": "Consumo discrecional",
    "consumer_staples": "Consumo básico",
    "corporate": "Deuda corporativa",
    "energy": "Energía",
    "financials": "Finanzas",
    "government": "Deuda pública",
    "health_care": "Salud",
    "industrials": "Industria",
    "information_technology": "Tecnología",
    "materials": "Materiales",
    "real_estate": "Inmobiliario",
    "utilities": "Servicios públicos",
    UNKNOWN_SECTOR: _OTHER_LABEL,
}
_CURRENCY_LABELS: Mapping[str, str] = {
    "AED": "Dírham",
    "AUD": "Dólar australiano",
    "BRL": "Real brasileño",
    "CAD": "Dólar canadiense",
    "CHF": "Franco suizo",
    "CNY": "Yuan",
    "DKK": "Corona danesa",
    "EUR": "Euro",
    "GBP": "Libra",
    "HKD": "Dólar de Hong Kong",
    "ILS": "Séquel",
    "INR": "Rupia india",
    "JPY": "Yen",
    "KRW": "Won",
    "MXN": "Peso mexicano",
    "NOK": "Corona noruega",
    "NZD": "Dólar neozelandés",
    "PLN": "Esloti",
    "SAR": "Riyal saudí",
    "SEK": "Corona sueca",
    "SGD": "Dólar de Singapur",
    "TWD": "Dólar taiwanés",
    "USD": "Dólar",
    "ZAR": "Rand",
    UNKNOWN_CURRENCY: _OTHER_LABEL,
}


@dataclass(frozen=True)
class Constituent:
    """Componente de una posición. `None` o vacío en país, sector o divisa significa desconocido."""

    key: str
    name: str
    weight: Decimal
    country: str | None
    sector: str | None
    currency: str | None


@dataclass(frozen=True)
class HoldingIn:
    """Posición valorada. Una acción directa es un fondo de un solo componente con peso 1."""

    asset_id: str
    name: str
    asset_type: AssetType
    value_eur: Decimal
    constituents: Sequence[Constituent]


@dataclass(frozen=True)
class ExposureResult:
    by_country: list[ExposureBucket]
    by_sector: list[ExposureBucket]
    by_currency: list[ExposureBucket]
    top_companies: list[TopCompany]
    overlap: list[OverlapItem]
    radiography: Radiography
    coverage_pct: Decimal


@dataclass
class _Company:
    key: str
    name: str
    value_eur: Decimal
    direct: bool
    held_in: list[tuple[str, Decimal, Decimal]]


def _weight(value: Decimal, total: Decimal) -> Decimal:
    if total == _ZERO:
        return _ZERO.quantize(_WEIGHT_STEP)
    return (value / total).quantize(_WEIGHT_STEP, rounding=ROUND_HALF_EVEN)


def _buckets(
    values: Mapping[str, Decimal], labels: Mapping[str, str], unknown: str, total: Decimal
) -> list[ExposureBucket]:
    """De mayor a menor, con lo desconocido siempre al final."""
    ordered = sorted(values.items(), key=lambda item: (item[0] == unknown, -item[1], item[0]))
    return [
        ExposureBucket(
            key=key, label=labels.get(key, key), value_eur=value, weight=_weight(value, total)
        )
        for key, value in ordered
    ]


def _is_company(key: str) -> bool:
    return not key.startswith(_NON_COMPANY_PREFIXES)


def _add(values: dict[str, Decimal], key: str, amount: Decimal) -> None:
    values[key] = values.get(key, _ZERO) + amount


def _collect_companies(holdings: Sequence[HoldingIn]) -> list[_Company]:
    companies: dict[str, _Company] = {}
    for holding in holdings:
        direct = holding.asset_type is AssetType.STOCK
        for part in holding.constituents:
            if not _is_company(part.key):
                continue
            amount = holding.value_eur * part.weight
            company = companies.setdefault(
                part.key, _Company(part.key, part.name, _ZERO, False, [])
            )
            company.value_eur += amount
            company.held_in.append((holding.asset_id, part.weight, amount))
            if direct and not company.direct:
                company.name, company.direct = part.name, True
    return sorted(companies.values(), key=lambda c: (-c.value_eur, c.key))


def _top_company(company: _Company, total: Decimal) -> TopCompany:
    held = sorted(company.held_in, key=lambda h: (-h[2], h[0]))
    return TopCompany(
        key=company.key,
        name=company.name,
        value_eur=company.value_eur,
        weight=_weight(company.value_eur, total),
        held_in=[CompanyHolding(asset_id=a, weight_in_asset=w) for a, w, _ in held],
    )


def _overlap(company: _Company, total: Decimal) -> OverlapItem:
    return OverlapItem(
        key=company.key,
        name=company.name,
        weight=_weight(company.value_eur, total),
        asset_ids=sorted(asset_id for asset_id, _, _ in company.held_in),
    )


def _top_country(by_country: Sequence[ExposureBucket]) -> TopCountry:
    for bucket in by_country:
        if bucket.key != UNKNOWN_COUNTRY:
            return TopCountry(key=bucket.key, label=bucket.label, weight=bucket.weight)
    return TopCountry(key=UNKNOWN_COUNTRY, label=_OTHER_LABEL, weight=_ZERO.quantize(_WEIGHT_STEP))


def compute_exposure(holdings: Sequence[HoldingIn]) -> ExposureResult:
    total = sum((h.value_eur for h in holdings), _ZERO)
    countries: dict[str, Decimal] = {}
    sectors: dict[str, Decimal] = {}
    currencies: dict[str, Decimal] = {}
    for holding in holdings:
        for part in holding.constituents:
            amount = holding.value_eur * part.weight
            _add(countries, part.country or UNKNOWN_COUNTRY, amount)
            _add(sectors, part.sector or UNKNOWN_SECTOR, amount)
            _add(currencies, part.currency or UNKNOWN_CURRENCY, amount)

    by_country = _buckets(countries, _COUNTRY_LABELS, UNKNOWN_COUNTRY, total)
    companies = _collect_companies(holdings)
    group_value = sum((c.value_eur for c in companies[:TOP_COMPANIES_GROUP_N]), _ZERO)
    known = sum((v for k, v in countries.items() if k != UNKNOWN_COUNTRY), _ZERO)
    return ExposureResult(
        by_country=by_country,
        by_sector=_buckets(sectors, _SECTOR_LABELS, UNKNOWN_SECTOR, total),
        by_currency=_buckets(currencies, _CURRENCY_LABELS, UNKNOWN_CURRENCY, total),
        top_companies=[_top_company(c, total) for c in companies[:TOP_COMPANIES_LIMIT]],
        overlap=[_overlap(c, total) for c in companies if len(c.held_in) >= 2],
        radiography=Radiography(
            num_holdings=sum(1 for h in holdings if h.asset_type in _FUND_TYPES),
            top_country=_top_country(by_country),
            top_companies_group=TopCompaniesGroup(
                n=TOP_COMPANIES_GROUP_N, weight=_weight(group_value, total)
            ),
        ),
        coverage_pct=_weight(known, total),
    )
