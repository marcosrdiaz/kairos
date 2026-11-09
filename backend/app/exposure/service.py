"""Interfaz pública de exposición y radar (diseño del MVP §4.2).

El radar se calcula en `radar.py` (reglas) y `radar_flow.py` (datos y trazas).
"""

import csv
from collections import defaultdict
from collections.abc import Collection, Iterable
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from app.core import trace
from app.exposure import engine, radar_flow, repository
from app.exposure.repository import CompositionRow
from app.portfolio import service as portfolio_service
from app.schemas.common import AssetType, SourceKind, SourceRef, TraceKind
from app.schemas.exposure import ExposureOut
from app.schemas.portfolio import PositionOut
from app.schemas.radar import RadarOut

COMPOSITIONS_DIR = Path(__file__).resolve().parents[3] / "data" / "seed" / "compositions"
"""En local, `<repo>/data/seed/compositions`; en Docker, `/data/seed/compositions`."""

_RESIDUAL_PREFIX = "OTROS_"


def load_compositions(directory: Path = COMPOSITIONS_DIR) -> int:
    """Carga los CSV de T1-08 en `composition`. Idempotente. Devuelve el número de filas."""
    rows: list[CompositionRow] = []
    for path in sorted(directory.glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as handle:
            rows += [
                CompositionRow(
                    fund_asset_id=path.stem,
                    constituent_key=raw["constituent_key"],
                    name=raw["name"],
                    weight=Decimal(raw["weight"]),
                    country=raw["country"] or None,
                    sector=raw["sector"] or None,
                    currency=raw["currency"] or None,
                    as_of=date.fromisoformat(raw["as_of"]),
                    source=raw["source"],
                )
                for raw in csv.DictReader(handle)
            ]
    return repository.replace_compositions(rows)


def company_weights(
    asset_ids: Iterable[str], companies: Collection[str]
) -> dict[str, dict[str, Decimal]]:
    """Peso de cada empresa en cada fondo o ETF: `{asset_id: {constituent_key: peso}}`.

    Solo incluye los pares con fila en la composición: sin fila, la empresa no está en el fondo.
    """
    if not companies:
        return {}
    weights: dict[str, dict[str, Decimal]] = defaultdict(dict)
    for row in repository.get_named_rows(asset_ids, companies):
        weights[row.fund_asset_id][row.constituent_key] = row.weight
    return dict(weights)


def _residual(position: PositionOut) -> engine.Constituent:
    """Posición sin composición: su país y su sector no se conocen, su divisa sí."""
    key = f"{_RESIDUAL_PREFIX}{position.asset_id}"
    return engine.Constituent(key, position.name, Decimal("1"), None, None, position.price_currency)


def _direct_stock(position: PositionOut, known: CompositionRow | None) -> engine.Constituent:
    """Acción directa: el país y el sector salen de su fila en las composiciones (D-052)."""
    return engine.Constituent(
        key=position.ticker or position.asset_id,
        name=position.name,
        weight=Decimal("1"),
        country=known.country if known else None,
        sector=known.sector if known else None,
        currency=position.price_currency,
    )


def _as_constituent(row: CompositionRow) -> engine.Constituent:
    return engine.Constituent(
        row.constituent_key, row.name, row.weight, row.country, row.sector, row.currency
    )


def _midnight(day: date) -> datetime:
    return datetime(day.year, day.month, day.day, tzinfo=UTC)


def get_exposure(portfolio_id: str) -> ExposureOut:
    """Look-through de la cartera. `as_of` es la composición más antigua de las que se usan."""
    valued = portfolio_service.get_valued(portfolio_id)  # 404 si no existe
    compositions: dict[str, list[CompositionRow]] = defaultdict(list)
    for row in repository.get_compositions(p.asset_id for p in valued.positions):
        compositions[row.fund_asset_id].append(row)
    stocks = {p.ticker for p in valued.positions if p.asset_type is AssetType.STOCK and p.ticker}
    known = repository.latest_by_key(stocks) if stocks else {}

    holdings: list[engine.HoldingIn] = []
    for p in valued.positions:
        parts: list[engine.Constituent]
        if p.asset_type is AssetType.STOCK and p.ticker:
            parts = [_direct_stock(p, known.get(p.ticker))]
        elif p.asset_id in compositions:
            parts = [_as_constituent(row) for row in compositions[p.asset_id]]
        else:
            parts = [_residual(p)]
        holdings.append(engine.HoldingIn(p.asset_id, p.name, p.asset_type, p.value_eur, parts))

    result = engine.compute_exposure(holdings)
    sources = [
        SourceRef(
            kind=SourceKind.COMPOSITION,
            label=rows[0].source,
            ref=asset_id,
            as_of=_midnight(rows[0].as_of),
        )
        for asset_id, rows in sorted(compositions.items())
    ]
    dates = [row.as_of for rows in compositions.values() for row in rows]
    calc_id = trace.record(
        TraceKind.EXPOSURE,
        engine.FORMULA,
        inputs={
            "portfolio_id": portfolio_id,
            "positions": [
                {"asset_id": h.asset_id, "value_eur": h.value_eur, "n_rows": len(h.constituents)}
                for h in holdings
            ],
        },
        outputs={
            "by_country": result.by_country,
            "by_sector": result.by_sector,
            "by_currency": result.by_currency,
            "radiography": result.radiography,
            "coverage_pct": result.coverage_pct,
        },
        sources=sources,
        parent_calc_ids=[valued.calc_id],
    )
    return ExposureOut(
        by_country=result.by_country,
        by_sector=result.by_sector,
        by_currency=result.by_currency,
        top_companies=result.top_companies,
        overlap=result.overlap,
        radiography=result.radiography,
        coverage_pct=result.coverage_pct,
        as_of=_midnight(min(dates)) if dates else valued.valued_at,
        calc_id=calc_id,
    )


def get_radar(portfolio_id: str) -> RadarOut:
    """Riesgos y oportunidades de la cartera (RF-18, SPEC §8.5). Una traza por aviso."""
    return radar_flow.get_radar(portfolio_id, get_exposure)
