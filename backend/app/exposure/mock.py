"""Mock de exposición y radar: sirve los ejemplos de `schemas/examples/` (D-018).

Sin BD ni cálculo. Lo sustituyen T1-11 y T2-05; se borra en T2-03.
"""

import csv
from collections.abc import Collection, Iterable
from decimal import Decimal
from pathlib import Path

from app.portfolio import service as portfolio_service
from app.schemas import examples
from app.schemas.exposure import ExposureOut
from app.schemas.radar import RadarOut

COMPOSITIONS_DIR = Path(__file__).resolve().parents[3] / "data" / "seed" / "compositions"


def company_weights(
    asset_ids: Iterable[str], companies: Collection[str]
) -> dict[str, dict[str, Decimal]]:
    """Lee los CSV de T1-08 hasta que T1-11 cargue la tabla `composition`."""
    weights: dict[str, dict[str, Decimal]] = {}
    for asset_id in asset_ids:
        path = COMPOSITIONS_DIR / f"{asset_id}.csv"
        if not companies or not path.is_file():
            continue
        with path.open(encoding="utf-8", newline="") as handle:
            found = {
                row["constituent_key"]: Decimal(row["weight"])
                for row in csv.DictReader(handle)
                if row["constituent_key"] in companies
            }
        if found:
            weights[asset_id] = found
    return weights


def get_exposure(portfolio_id: str) -> ExposureOut:
    portfolio_service.ensure_exists(portfolio_id)  # 404 si no existe
    return ExposureOut.model_validate(examples.load("ExposureOut"))


def get_radar(portfolio_id: str) -> RadarOut:
    portfolio_service.ensure_exists(portfolio_id)  # 404 si no existe
    return RadarOut.model_validate(examples.load("RadarOut"))
