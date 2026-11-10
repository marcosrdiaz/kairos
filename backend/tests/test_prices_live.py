"""Precios en directo (T2-24, D-065): proveedor Yahoo con caché en BD, caducidad y fallos.

Sin red: la fuente de Yahoo es falsa (`FakeChartSource`) o un `httpx.MockTransport`. El único
test con red es `test_live_yahoo_values_laura`, marcado `live` (no corre en CI).
"""

from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.core import clock
from app.core.errors import AppError, ErrorCode
from app.main import API_PREFIX
from app.prices import service
from app.prices.live import NAV_TTL, PRICE_TTL, LiveProvider
from app.prices.yahoo import Chart, ProviderError, YahooClient, parse_chart

STOCK = "US67066G1040"  # NVIDIA, intradía en USD (NVDA)
FUND = "IE00B03HD191"  # fondo Vanguard, VL diario (0P00000WLG.F)
T0 = datetime(2026, 11, 10, 15, 0, tzinfo=UTC)


def _chart(
    closes: dict[str, str],
    last: tuple[datetime, str] | None = None,
    market_open: bool = True,
    next_open: datetime | None = None,
) -> Chart:
    return Chart(
        closes=[(date.fromisoformat(d), Decimal(v)) for d, v in sorted(closes.items())],
        last_at=last[0] if last else None,
        last_price=Decimal(last[1]) if last else None,
        market_open=market_open,
        next_open=next_open,
    )


class FakeChartSource:
    """Devuelve el `Chart` preparado para cada símbolo y apunta cada llamada."""

    def __init__(self, charts: dict[str, Chart]) -> None:
        self.charts = charts
        self.calls: list[tuple[str, str]] = []
        self.fail = False

    def chart(self, symbol: str, range_: str) -> Chart:
        self.calls.append((symbol, range_))
        if self.fail:
            raise ProviderError(f"{symbol}: sin respuesta")
        return self.charts[symbol]


@pytest.fixture
def now() -> Iterator[None]:
    clock.set_now(T0)
    yield


@pytest.fixture
def source(db: None, now: None) -> Iterator[FakeChartSource]:
    from app.portfolio import service as portfolio_service

    portfolio_service.load_seed(portfolios=False)  # `price.asset_id` apunta a `asset` (FK)
    fake = FakeChartSource(
        {
            "NVDA": _chart(
                {"2026-11-06": "140.00", "2026-11-09": "142.00"},
                last=(T0 - timedelta(minutes=1), "145.50"),
            ),
            "0P00000WLG.F": _chart(
                {"2026-11-06": "30.10", "2026-11-09": "30.20"},
                last=(datetime(2026, 11, 9, 22, 0, tzinfo=UTC), "30.20"),
            ),
            "EURUSD=X": _chart(
                {"2026-11-09": "1.1600"}, last=(T0 - timedelta(seconds=30), "1.1650")
            ),
        }
    )
    previous = service.set_provider(LiveProvider(fake))
    yield fake
    service.set_provider(previous)


# --- Lectura de la respuesta de Yahoo ---


def _payload(**meta: Any) -> dict[str, Any]:
    base_meta = {
        "regularMarketPrice": Decimal("145.5"),
        "regularMarketTime": int((T0 - timedelta(minutes=1)).timestamp()),
        "currentTradingPeriod": {
            "regular": {
                "start": int(datetime(2026, 11, 10, 14, 30, tzinfo=UTC).timestamp()),
                "end": int(datetime(2026, 11, 10, 21, 0, tzinfo=UTC).timestamp()),
            }
        },
    }
    base_meta.update(meta)
    stamps = [datetime(2026, 11, d, 14, 30, tzinfo=UTC) for d in (6, 9, 10)]
    return {
        "chart": {
            "result": [
                {
                    "meta": base_meta,
                    "timestamp": [int(s.timestamp()) for s in stamps],
                    "indicators": {
                        "quote": [{"close": [Decimal("140"), None, Decimal("145.123456789")]}]
                    },
                }
            ]
        }
    }


def test_parse_chart_reads_closes_last_price_and_session() -> None:
    chart = parse_chart(_payload(), T0)
    assert chart.closes == [
        (date(2026, 11, 6), Decimal("140.00000000")),
        (date(2026, 11, 10), Decimal("145.12345679")),
    ]
    assert chart.last_price == Decimal("145.50000000")
    assert chart.last_at == T0 - timedelta(minutes=1)
    assert chart.market_open is True
    assert chart.next_open is None


def test_parse_chart_before_the_open_knows_when_it_opens() -> None:
    early = datetime(2026, 11, 10, 9, 0, tzinfo=UTC)
    chart = parse_chart(_payload(), early)
    assert chart.market_open is False
    assert chart.next_open == datetime(2026, 11, 10, 14, 30, tzinfo=UTC)


def test_parse_chart_rejects_an_empty_answer() -> None:
    with pytest.raises(ProviderError):
        parse_chart({"chart": {"result": None, "error": {"code": "Not Found"}}}, T0)


def test_yahoo_client_asks_the_chart_endpoint_and_parses_decimals(now: None) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        body = _payload()
        text = httpx.Response(200, json=_json_ready(body)).text
        return httpx.Response(200, text=text, headers={"content-type": "application/json"})

    client = YahooClient(httpx.Client(transport=httpx.MockTransport(handler)))
    chart = client.chart("NVDA", "5d")
    assert seen[0].url.path.endswith("/v8/finance/chart/NVDA")
    assert seen[0].url.params["range"] == "5d"
    assert seen[0].url.params["interval"] == "1d"
    assert chart.last_price == Decimal("145.50000000")


def test_yahoo_client_turns_http_errors_into_provider_errors(now: None) -> None:
    client = YahooClient(httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(429))))
    with pytest.raises(ProviderError):
        client.chart("NVDA", "5d")


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value) if value != value.to_integral() else int(value)
    if isinstance(value, dict):
        return {k: _json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_ready(v) for v in value]
    return value


# --- Caducidad y caché ---


def test_latest_uses_the_live_quote_with_its_real_time(source: FakeChartSource) -> None:
    price = service.latest(STOCK)
    assert price.price == Decimal("145.50")
    assert price.price_at == T0 - timedelta(minutes=1)
    assert price.currency == "USD"
    assert source.calls == [("NVDA", "3y")]


def test_a_quote_younger_than_a_minute_is_not_asked_again(source: FakeChartSource) -> None:
    service.latest(STOCK)
    clock.set_now(T0 + PRICE_TTL - timedelta(seconds=1))
    service.latest(STOCK)
    assert len(source.calls) == 1


def test_after_a_minute_it_asks_again_only_for_the_last_days(source: FakeChartSource) -> None:
    service.latest(STOCK)
    clock.set_now(T0 + PRICE_TTL)
    source.charts["NVDA"] = _chart({"2026-11-10": "146.00"}, last=(T0 + PRICE_TTL, "146.25"))
    price = service.latest(STOCK)
    assert source.calls == [("NVDA", "3y"), ("NVDA", "5d")]
    assert price.price == Decimal("146.25")


def test_fund_nav_is_asked_at_most_every_six_hours(source: FakeChartSource) -> None:
    service.latest(FUND)
    clock.set_now(T0 + NAV_TTL - timedelta(minutes=1))
    service.latest(FUND)
    assert len(source.calls) == 1
    clock.set_now(T0 + NAV_TTL)
    service.latest(FUND)
    assert len(source.calls) == 2


def test_with_the_market_closed_it_waits_for_the_open(source: FakeChartSource) -> None:
    opens = T0 + timedelta(hours=10)
    source.charts["NVDA"] = _chart(
        {"2026-11-09": "142.00"},
        last=(T0 - timedelta(hours=3), "142.00"),
        market_open=False,
        next_open=opens,
    )
    service.latest(STOCK)
    clock.set_now(opens - timedelta(minutes=1))
    service.latest(STOCK)
    assert len(source.calls) == 1
    clock.set_now(opens)
    service.latest(STOCK)
    assert len(source.calls) == 2


def test_prices_survive_a_restart_from_the_database(source: FakeChartSource) -> None:
    service.latest(STOCK)
    fresh = FakeChartSource({})
    fresh.fail = True
    service.set_provider(LiveProvider(fresh))
    price = service.latest(STOCK)
    assert price.price == Decimal("145.50")
    assert fresh.calls == [("NVDA", "5d")]  # sabe que ya hay histórico guardado


def test_history_combines_stored_closes_and_live_quote(source: FakeChartSource) -> None:
    points = service.history(STOCK, date(2026, 11, 1), date(2026, 11, 10))
    assert [(p.price_at.date(), p.price) for p in points] == [
        (date(2026, 11, 6), Decimal("140.00")),
        (date(2026, 11, 9), Decimal("142.00")),
        (date(2026, 11, 10), Decimal("145.50")),
    ]
    previous = service.previous_close(STOCK, date(2026, 11, 10))
    assert previous is not None and previous.price == Decimal("142.00")


def test_fx_comes_from_eurusd_live(source: FakeChartSource) -> None:
    quote = service.fx_quote("EURUSD")
    assert quote.rate == Decimal("1.1650")
    assert quote.at == T0 - timedelta(seconds=30)
    assert service.fx_rate("USDEUR") == (Decimal(1) / Decimal("1.1650")).quantize(
        Decimal("0.00000001")
    )
    assert ("EURUSD=X", "3y") in source.calls
    assert not any(symbol.startswith("USDEUR") for symbol, _ in source.calls)


def test_float_noise_is_rounded_like_the_csv(source: FakeChartSource) -> None:
    source.charts["NVDA"] = _chart(
        {"2026-11-09": "128.52000427"}, last=(T0 - timedelta(minutes=1), "128.60000610")
    )
    source.charts["EURUSD=X"] = _chart({}, last=(T0, "1.11931944"))
    assert service.history(STOCK, date(2026, 11, 9), date(2026, 11, 9))[0].price == Decimal(
        "128.5200"
    )
    assert service.latest(STOCK).price == Decimal("128.6000")
    assert service.fx_rate("EURUSD") == Decimal("1.119319")


def test_fixed_price_assets_never_call_the_provider(source: FakeChartSource) -> None:
    assert service.latest("DEP-12M").price > 0
    assert source.calls == []


# --- Fallos ---


def test_if_the_provider_fails_the_last_stored_price_is_served(
    source: FakeChartSource,
) -> None:
    service.latest(STOCK)
    clock.set_now(T0 + timedelta(minutes=5))
    source.fail = True
    price = service.latest(STOCK)
    assert price.price == Decimal("145.50")
    assert price.price_at == T0 - timedelta(minutes=1)  # su fecha real, no la de ahora
    assert "último precio guardado" in price.source.label


def test_a_failure_does_not_hammer_the_provider(source: FakeChartSource) -> None:
    source.fail = True
    with pytest.raises(AppError):
        service.latest(STOCK)
    with pytest.raises(AppError):
        service.latest(STOCK)
    assert len(source.calls) == 1


def test_without_any_stored_price_it_is_unavailable(source: FakeChartSource) -> None:
    source.fail = True
    with pytest.raises(AppError) as error:
        service.latest(STOCK)
    assert error.value.code is ErrorCode.PRICE_UNAVAILABLE


# --- Modo y arranque ---


def test_production_with_the_offline_provider_does_not_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "offline")
    with pytest.raises(ValidationError, match="MARKET_DATA_PROVIDER=yahoo"):
        Settings()


def test_an_unknown_provider_does_not_start(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "twelvedata")
    with pytest.raises(ValidationError):
        Settings()


def test_the_provider_follows_the_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    previous = service.set_provider(None)
    try:
        monkeypatch.setenv("DEMO_MODE", "false")
        monkeypatch.setenv("MARKET_DATA_PROVIDER", "yahoo")
        get_settings.cache_clear()
        assert isinstance(service.get_provider(), LiveProvider)
    finally:
        service.set_provider(previous)


def test_health_shows_the_mode_and_provider(client: TestClient) -> None:
    body = client.get(f"{API_PREFIX}/health").json()
    assert body["mode"] == "demo"
    assert body["market_data_provider"] == "offline"


# --- Con red (no corre en CI) ---


@pytest.mark.live
def test_live_yahoo_values_laura(client: TestClient) -> None:
    clock.set_now(None)
    previous = service.set_provider(LiveProvider())
    try:
        response = client.get(f"{API_PREFIX}/portfolios/laura")
        assert response.status_code == 200, response.text
        body = response.json()
        stamps = [p["price_at"] for p in body["positions"] if p["price_kind"] == "intraday"]
        assert stamps and max(stamps) > "2026-11-06T23:59:59Z"
    finally:
        service.set_provider(previous)
