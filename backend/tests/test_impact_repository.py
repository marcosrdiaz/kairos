"""`impact/repository.py`: escritura idempotente y lectura de `factor_beta`."""

from datetime import date
from decimal import Decimal

import pytest

from app.core.db import session_scope
from app.impact import repository
from app.impact.betas import BetaEstimate
from app.portfolio.models import Asset
from app.schemas.common import Factor


def _asset(asset_id: str) -> Asset:
    return Asset(
        id=asset_id,
        isin=None,
        ticker=None,
        name=asset_id,
        asset_type="etf",
        asset_class="equity",
        currency="EUR",
        ter=None,
        transferable=False,
        price_kind="nav",
        price_source="fixed:1",
    )


def _est(asset_id: str, factor: Factor, beta: str) -> BetaEstimate:
    return BetaEstimate(
        asset_id=asset_id,
        factor=factor,
        beta=Decimal(beta),
        std_err=Decimal("0.01000000"),
        r2=Decimal("0.80000000"),
        n_obs=700,
        window_start=date(2023, 11, 7),
        window_end=date(2026, 11, 6),
    )


@pytest.fixture
def assets(db: None) -> None:
    with session_scope() as session:
        session.add_all([_asset("A"), _asset("B")])


def test_replace_betas_is_idempotent_and_only_touches_given_assets(assets: None) -> None:
    repository.replace_betas([_est("A", Factor.EQ_GLOBAL, "1.0"), _est("B", Factor.OIL, "0.2")])
    repository.replace_betas([_est("A", Factor.EQ_GLOBAL, "0.9"), _est("A", Factor.OIL, "0.1")])
    repository.replace_betas([_est("A", Factor.EQ_GLOBAL, "0.9"), _est("A", Factor.OIL, "0.1")])

    got = repository.get_betas(["A", "B"])

    assert {(e.asset_id, e.factor, e.beta) for e in got} == {
        ("A", Factor.EQ_GLOBAL, Decimal("0.9")),
        ("A", Factor.OIL, Decimal("0.1")),
        ("B", Factor.OIL, Decimal("0.2")),
    }


def test_get_betas_round_trips_all_fields(assets: None) -> None:
    original = _est("A", Factor.RATES_EUR, "-6.50000000")
    repository.replace_betas([original])

    assert repository.get_betas(["A"]) == [original]
    assert repository.get_betas(["B"]) == []
