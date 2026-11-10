"""Catálogo abierto (T4-07): `POST /assets` da de alta un activo que no está en `assets.json`,
lo valora con el proveedor en directo y le calcula las betas. Sin red: Yahoo es falso."""

from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.core import clock
from app.impact import repository as impact_repository
from app.prices import service as prices_service
from app.prices.discover import asset_class_for, discover
from app.prices.live import LiveProvider
from app.prices.provider import PricePoint
from app.prices.yahoo import Chart, ProviderError, Quote
from app.schemas.common import AssetClass, AssetType, Factor

NOW = datetime(2026, 11, 6, 18, 0, tzinfo=UTC)
NEW_ISIN = "IE00BFY0GT14"  # no está en assets.json
SYMBOL = "SPPW.DE"
NEW_PORTFOLIO = {"name": "Hijos", "kind": "family", "risk_profile": "moderado"}
N_DAYS = 300
START = date(2025, 9, 1)


def _days() -> list[date]:
    return [START + timedelta(days=i) for i in range(N_DAYS + 1)]


def _levels(start: float, returns: np.ndarray) -> list[Decimal]:
    levels = [start]
    for r in returns:
        levels.append(levels[-1] * (1 + float(r)))
    return [Decimal(repr(round(v, 4))) for v in levels]


rng = np.random.default_rng(11)
MOVES = {f: rng.normal(0, 0.01, N_DAYS) for f in Factor}
MOVES[Factor.RATES_EUR] = rng.normal(0, 0.0005, N_DAYS)
ASSET_CLOSES = list(zip(_days(), _levels(30.0, 1.1 * MOVES[Factor.EQ_GLOBAL]), strict=True))


class FakeYahoo:
    """Búsqueda y cierres de Yahoo en memoria."""

    def __init__(self) -> None:
        self.quotes: dict[str, list[Quote]] = {
            NEW_ISIN: [
                Quote("SPPW.DE", "SPDR MSCI World UCITS ETF", "ETF"),
            ],
            "BONDS": [Quote("IBGL.AS", "iShares Euro Government Bond 15-30yr", "ETF")],
            "PENCE": [
                Quote("VWRL.L", "Vanguard FTSE All-World (GBp)", "ETF"),
                Quote("VWRL.AS", "Vanguard FTSE All-World", "ETF"),
            ],
        }
        self.currency = {"SPPW.DE": "EUR", "IBGL.AS": "EUR", "VWRL.L": "GBp", "VWRL.AS": "EUR"}
        self.searches: list[str] = []
        self.down = False

    def search(self, query: str) -> list[Quote]:
        self.searches.append(query)
        if self.down:
            raise ProviderError("sin conexión")
        return list(self.quotes.get(query.upper(), []))

    def chart(self, symbol: str, range_: str) -> Chart:
        if self.down:
            raise ProviderError("sin conexión")
        return Chart(
            closes=list(ASSET_CLOSES),
            last_price=None,
            last_at=None,
            market_open=False,
            next_open=None,
            currency=self.currency.get(symbol, "EUR"),
        )


class FakeFactors:
    def factor_closes(self, factor: Factor) -> list[PricePoint]:
        values = (
            [Decimal(repr(round(float(v), 10))) for v in 0.025 + np.cumsum([0.0, *MOVES[factor]])]
            if factor is Factor.RATES_EUR
            else _levels(100.0, MOVES[factor])
        )
        return [PricePoint(day=d, value=v) for d, v in zip(_days(), values, strict=True)]

    def source_of(self, factor: Factor, day: date) -> str | None:
        return "csv:test"


@pytest.fixture
def yahoo(client: TestClient) -> Iterator[FakeYahoo]:
    clock.set_now(NOW)
    fake = FakeYahoo()
    previous_search = prices_service.set_search_source(fake)
    previous_provider = prices_service.set_provider(LiveProvider(fake))
    previous_factors = prices_service.set_factor_source(FakeFactors())
    try:
        yield fake
    finally:
        prices_service.set_search_source(previous_search)
        prices_service.set_provider(previous_provider)
        prices_service.set_factor_source(previous_factors)
        clock.reset()


def test_registers_an_etf_outside_the_catalog(client: TestClient, yahoo: FakeYahoo) -> None:
    response = client.post("/api/v1/assets", json={"query": NEW_ISIN})

    assert response.status_code == 201, response.json()
    asset = response.json()
    assert asset["id"] == NEW_ISIN
    assert asset["isin"] == NEW_ISIN
    assert asset["ticker"] == "SPPW"
    assert asset["asset_type"] == "etf"
    assert asset["asset_class"] == "equity"
    assert asset["currency"] == "EUR"
    assert asset["price_kind"] == "intraday"
    assert asset["transferable"] is False
    lookup = client.get("/api/v1/assets/lookup", params={"q": "SPDR MSCI"}).json()
    assert [a["id"] for a in lookup] == [NEW_ISIN]


def test_the_new_asset_gets_betas(client: TestClient, yahoo: FakeYahoo) -> None:
    client.post("/api/v1/assets", json={"query": NEW_ISIN})

    betas = {b.factor: b for b in impact_repository.get_betas([NEW_ISIN])}
    assert set(betas) == set(Factor)
    assert abs(betas[Factor.EQ_GLOBAL].beta - Decimal("1.1")) < Decimal("0.01")


def test_the_new_asset_can_be_held_and_valued(client: TestClient, yahoo: FakeYahoo) -> None:
    client.post("/api/v1/assets", json={"query": NEW_ISIN})
    created = client.post("/api/v1/portfolios", json=NEW_PORTFOLIO).json()

    response = client.post(
        f"/api/v1/portfolios/{created['id']}/positions",
        json={"positions": [{"asset_id": NEW_ISIN, "units": "10", "avg_cost_eur": "25.00"}]},
    )

    assert response.status_code in (200, 201), response.json()
    valued = client.get(f"/api/v1/portfolios/{created['id']}").json()
    [position] = valued["positions"]
    last_close = ASSET_CLOSES[-1][1]
    assert Decimal(position["value_eur"]) == (10 * last_close).quantize(Decimal("0.01"))


def test_exposure_shows_lower_coverage_for_an_asset_without_composition(
    client: TestClient, yahoo: FakeYahoo
) -> None:
    client.post("/api/v1/assets", json={"query": NEW_ISIN})
    created = client.post("/api/v1/portfolios", json=NEW_PORTFOLIO).json()
    client.post(
        f"/api/v1/portfolios/{created['id']}/positions",
        json={"positions": [{"asset_id": NEW_ISIN, "units": "10", "avg_cost_eur": "25.00"}]},
    )

    exposure = client.get(f"/api/v1/portfolios/{created['id']}/exposure").json()

    assert Decimal(exposure["coverage_pct"]) < Decimal("0.9")


def test_registering_twice_returns_the_same_asset(client: TestClient, yahoo: FakeYahoo) -> None:
    first = client.post("/api/v1/assets", json={"query": NEW_ISIN}).json()
    second = client.post("/api/v1/assets", json={"query": SYMBOL}).json()

    assert second == first
    assert yahoo.searches == [NEW_ISIN]  # la segunda la resuelve el catálogo, sin buscar


def test_a_catalog_asset_is_returned_without_searching(
    client: TestClient, yahoo: FakeYahoo
) -> None:
    response = client.post("/api/v1/assets", json={"query": "ie00b4l5y983"})

    assert response.status_code == 201
    assert response.json()["id"] == "IE00B4L5Y983"
    assert yahoo.searches == []


def test_unknown_asset_gives_a_clear_error(client: TestClient, yahoo: FakeYahoo) -> None:
    response = client.post("/api/v1/assets", json={"query": "NOEXISTE123"})

    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "NOT_FOUND"
    assert "NOEXISTE123" in body["message"]


def test_provider_down_gives_503(client: TestClient, yahoo: FakeYahoo) -> None:
    yahoo.down = True

    response = client.post("/api/v1/assets", json={"query": NEW_ISIN})

    assert response.status_code == 503
    assert response.json()["code"] == "UPSTREAM_UNAVAILABLE"


def test_demo_mode_cannot_register_new_assets(client: TestClient) -> None:
    response = client.post("/api/v1/assets", json={"query": NEW_ISIN})

    assert response.status_code == 503
    assert "demo" in response.json()["message"]


# --- Búsqueda (pura) ---


def test_quotes_in_pence_are_skipped() -> None:
    found = discover("PENCE", FakeYahoo())

    assert found is not None
    assert found.symbol == "VWRL.AS"  # VWRL.L cotiza en peniques: se salta


def test_an_isin_prefers_the_euro_listing() -> None:
    yahoo = FakeYahoo()
    yahoo.quotes["IE00B3XXRP09"] = [
        Quote("VUSD.L", "Vanguard S&P 500 UCITS ETF", "ETF"),
        Quote("VUSA.AS", "Vanguard S&P 500 UCITS ETF", "ETF"),
    ]
    yahoo.currency.update({"VUSD.L": "USD", "VUSA.AS": "EUR"})

    found = discover("IE00B3XXRP09", yahoo)

    assert found is not None
    assert (found.symbol, found.currency) == ("VUSA.AS", "EUR")


def test_an_isin_without_euro_listing_takes_the_dollar_one() -> None:
    yahoo = FakeYahoo()
    yahoo.quotes["US0231351067"] = [Quote("AMZN", "Amazon.com, Inc.", "EQUITY")]
    yahoo.currency["AMZN"] = "USD"

    found = discover("US0231351067", yahoo)

    assert found is not None
    assert (found.symbol, found.currency) == ("AMZN", "USD")


def test_a_name_keeps_the_first_usable_result() -> None:
    yahoo = FakeYahoo()
    yahoo.quotes["APPLE"] = [
        Quote("AAPL", "Apple Inc.", "EQUITY"),
        Quote("APC.DE", "Apple Inc.", "EQUITY"),
    ]
    yahoo.currency.update({"AAPL": "USD", "APC.DE": "EUR"})

    found = discover("Apple", yahoo)

    assert found is not None
    assert found.symbol == "AAPL"


def test_bond_etfs_are_fixed_income() -> None:
    found = discover("BONDS", FakeYahoo())

    assert found is not None
    assert found.asset_class is AssetClass.FIXED_INCOME
    assert asset_class_for(AssetType.STOCK, "Treasury Wine Estates") is AssetClass.EQUITY


def test_funds_are_nav_daily_and_transferable(client: TestClient, yahoo: FakeYahoo) -> None:
    yahoo.quotes["FONDO"] = [Quote("0P0000XYZ.F", "Fondo Indexado Global", "MUTUALFUND")]

    asset = client.post("/api/v1/assets", json={"query": "FONDO"}).json()

    assert asset["id"] == "YF-0P0000XYZ.F"
    assert asset["isin"] is None
    assert asset["asset_type"] == "fund"
    assert asset["price_kind"] == "nav_daily"
    assert asset["transferable"] is True
