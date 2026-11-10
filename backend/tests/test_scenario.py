"""Escenarios ¿Y si…? (`SPEC.md` §8.3, RF-21, RNF-05): impacto por activo y latencia < 500 ms."""

import statistics
import time
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core import clock
from app.impact import repository
from app.impact.betas import BetaEstimate
from app.main import API_PREFIX
from app.portfolio import service as portfolio_service
from app.schemas.common import Factor

NOW = datetime(2026, 11, 8, 18, 0, tzinfo=UTC)
NO_PRICE = {"DEP-12M", "PP-MIXTO"}
URL = f"{API_PREFIX}/portfolios/laura/scenarios"
LATENCY_LIMIT_S = 0.5
BETAS = ((Factor.EQ_GLOBAL, Decimal("1")), (Factor.RATES_EUR, Decimal("-4")))


@pytest.fixture
def betas(client: TestClient) -> None:
    """Betas sintéticas a `EQ_GLOBAL` (β 1) y `RATES_EUR` (β −4) para los activos con precio."""
    clock.set_now(NOW)
    ids: set[str] = set()
    for portfolio in ("laura", "javier"):
        ids |= {p.asset_id for p in portfolio_service.get_valued(portfolio).positions}
    ids -= NO_PRICE
    repository.replace_betas(
        [
            BetaEstimate(
                asset_id=asset_id,
                factor=factor,
                beta=beta,
                std_err=Decimal("0.01"),
                r2=Decimal("0.8"),
                n_obs=700,
                window_start=date(2023, 11, 7),
                window_end=date(2026, 11, 6),
            )
            for asset_id in ids
            for factor, beta in BETAS
        ]
    )


def test_breakdown_is_per_asset_and_adds_up_to_the_total(betas: None, client: TestClient) -> None:
    body = client.post(URL, json={"factor_shocks": {"EQ_GLOBAL": "-0.10"}}).json()
    priced = {p.asset_id for p in portfolio_service.get_valued("laura").positions} - NO_PRICE
    assert {b["asset_id"] for b in body["breakdown"]} <= priced
    assert body["breakdown"], "el escenario debe repartir el impacto por activo"
    total = sum((Decimal(b["impact_eur"]) for b in body["breakdown"]), Decimal("0"))
    assert abs(total - Decimal(body["impact_eur"])) <= Decimal("0.05")
    assert all(Decimal(b["impact_eur"]) < 0 for b in body["breakdown"])


def test_several_factors_combine(betas: None, client: TestClient) -> None:
    equity = client.post(URL, json={"factor_shocks": {"EQ_GLOBAL": "-0.10"}}).json()
    rates = client.post(URL, json={"factor_shocks": {"RATES_EUR": "0.01"}}).json()
    both = client.post(
        URL, json={"factor_shocks": {"EQ_GLOBAL": "-0.10", "RATES_EUR": "0.01"}}
    ).json()
    expected = Decimal(equity["impact_eur"]) + Decimal(rates["impact_eur"])
    assert abs(Decimal(both["impact_eur"]) - expected) <= Decimal("0.05")


def test_zero_shock_has_no_impact(betas: None, client: TestClient) -> None:
    body = client.post(URL, json={"factor_shocks": {"OIL": "0"}}).json()
    assert Decimal(body["impact_eur"]) == 0


def test_unknown_portfolio_is_not_found(client: TestClient) -> None:
    response = client.post(
        f"{API_PREFIX}/portfolios/nadie/scenarios", json={"factor_shocks": {"EQ_GLOBAL": "-0.1"}}
    )
    assert response.status_code == 404


def test_scenario_answers_in_under_500_ms(betas: None, client: TestClient) -> None:
    """RNF-05. Mediana de 5 llamadas tras una de calentamiento (con `-n auto` hay ruido de CPU)."""
    payload = {"factor_shocks": {"EQ_GLOBAL": "-0.10", "EURUSD": "0.05"}}
    assert client.post(URL, json=payload).status_code == 200
    timings: list[float] = []
    for _ in range(5):
        start = time.perf_counter()
        response = client.post(URL, json=payload)
        timings.append(time.perf_counter() - start)
        assert response.status_code == 200
    assert statistics.median(timings) < LATENCY_LIMIT_S, timings
