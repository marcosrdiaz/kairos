"""Rango del impacto en cada posición (T2-23): `low_eur`/`high_eur` por activo.

Mismo término de incertidumbre que el rango total (`SPEC.md` §8.2, D-051), aplicado a un activo:
`I_i ± 1,28 · V_i · (1 − Σ_c w_c) · Σ_f u_f`.
"""

from datetime import UTC, date, datetime
from decimal import Decimal as D

from fastapi.testclient import TestClient

from app.core import clock
from app.impact import repository, service
from app.impact.betas import BetaEstimate
from app.impact.engine import PositionIn, ShocksIn, compute_impact
from app.portfolio import service as portfolio_service
from app.schemas.common import AssetClass, Factor

EQ = Factor.EQ_GLOBAL
FX = Factor.EURUSD


def beta(factor: Factor, value: str, se: str, asset_id: str = "A") -> BetaEstimate:
    return BetaEstimate(
        asset_id=asset_id,
        factor=factor,
        beta=D(value),
        std_err=D(se),
        r2=D("0.8"),
        n_obs=700,
        window_start=date(2023, 11, 7),
        window_end=date(2026, 11, 6),
    )


def position(asset_id: str, value: str, *betas: BetaEstimate, currency: str = "EUR") -> PositionIn:
    return PositionIn(
        asset_id=asset_id,
        name=asset_id,
        asset_class=AssetClass.EQUITY,
        currency=currency,
        value_eur=D(value),
        betas=betas,
    )


def shocks(**factors: str) -> ShocksIn:
    return ShocksIn({Factor[f]: D(s) for f, s in factors.items()}, {}, {})


def test_single_asset_range_is_the_total_range() -> None:
    # I = 1000 · 0,8 · −0,02 = −16; término = 1000 · 0,1 · 0,02 = 2; ±1,28 · 2 = ±2,56.
    result = compute_impact(
        [position("A", "1000", beta(EQ, "0.8", "0.1"))], shocks(EQ_GLOBAL="-0.02"), D(1)
    )

    (asset,) = result.assets
    assert (asset.low_eur, asset.impact_eur, asset.high_eur) == (
        D("-18.56"),
        D("-16.00"),
        D("-13.44"),
    )
    assert (asset.low_eur, asset.high_eur) == (result.low_eur, result.high_eur)


def test_not_significant_beta_widens_the_asset_range() -> None:
    # β 0,1 con se 0,1 no es significativa: impacto 0 y término = 1000 · (0,1 + 0,1) · 0,02 = 4.
    result = compute_impact(
        [position("A", "1000", beta(EQ, "0.1", "0.1"))], shocks(EQ_GLOBAL="-0.02"), D(1)
    )

    (asset,) = result.assets
    assert (asset.low_eur, asset.impact_eur, asset.high_eur) == (D("-5.12"), D("0.00"), D("5.12"))


def test_each_asset_has_its_own_range_and_the_total_is_narrower_than_their_sum() -> None:
    positions = [
        position("A", "1000", beta(EQ, "0.8", "0.1")),
        position("B", "3000", beta(EQ, "1.2", "0.05", asset_id="B")),
    ]
    result = compute_impact(positions, shocks(EQ_GLOBAL="-0.02"), D(1))

    a, b = result.assets
    assert (a.low_eur, a.high_eur) == (D("-18.56"), D("-13.44"))
    # B: I = 3000 · 1,2 · −0,02 = −72; término = 3000 · 0,05 · 0,02 = 3; ±3,84.
    assert (b.low_eur, b.impact_eur, b.high_eur) == (D("-75.84"), D("-72.00"), D("-68.16"))
    widths = D("5.12") + D("7.68")
    assert result.high_eur - result.low_eur < widths  # errores independientes (D-051)


def test_asset_without_betas_has_a_point_range() -> None:
    # Sin betas no hay incertidumbre estimada: solo el efecto dólar, sin rango.
    result = compute_impact([position("A", "1160", currency="USD")], shocks(EURUSD="0.16"), D(1))

    (asset,) = result.assets
    assert asset.low_eur == asset.impact_eur == asset.high_eur == D("-160.00")


def test_breakdown_carries_the_range(client: TestClient) -> None:
    clock.set_now(datetime(2026, 11, 8, 18, tzinfo=UTC))
    ids = {p.asset_id for p in portfolio_service.get_valued("laura").positions}
    repository.replace_betas([beta(EQ, "1", "0.01", asset_id=asset_id) for asset_id in ids])

    out = service.estimate_scenario("laura", {EQ: D("-0.10")})

    assert out.breakdown
    for asset in out.breakdown:
        assert asset.low_eur is not None and asset.high_eur is not None
        assert asset.low_eur < asset.impact_eur < asset.high_eur
