"""Impacto de una noticia en la cartera (T4-30): funciones puras y ruta con datos reales.

La ruta usa los CSV de `data/prices` (hasta el 6 nov) y la cartera de Laura. Regla 1: el LLM solo
elige canales y dirección; los números salen del motor con datos de mercado.
"""

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from fastapi.testclient import TestClient

from app.core import clock
from app.impact import news_estimate
from app.main import API_PREFIX
from app.news import repository
from app.news.ingest.sources import RawNews
from app.schemas.common import AssetType, PriceKind
from app.schemas.news import EffectTiming, NewsDirection

NVDA = "US67066G1040"
URL = f"{API_PREFIX}/portfolios/laura/news"


# --- Funciones puras ---


def _series(moves: list[float]) -> list[tuple[date, Decimal]]:
    value = Decimal("100")
    out = [(date(2024, 1, 1), value)]
    for i, move in enumerate(moves, start=1):
        value = value * (1 + Decimal(str(move)))
        out.append((date.fromordinal(date(2024, 1, 1).toordinal() + i), value))
    return out


def test_move_band_uses_strong_news_days_only() -> None:
    moves = ([0.001, -0.001] * 20 + [0.05, 0.0, 0.0, 0.0, 0.0]) * 6
    band = news_estimate.move_band(_series(moves), date(2025, 6, 1), horizon=1, min_events=5)
    assert band is not None and band.n >= 6
    assert band.p25 > Decimal("0.04")  # solo los días de movimiento fuerte


def test_move_band_needs_enough_cases() -> None:
    assert news_estimate.move_band(_series([0.01, -0.01] * 5), date(2025, 6, 1)) is None


def test_direction_sets_the_sign_and_uncertain_is_symmetric() -> None:
    band = news_estimate.Band(Decimal("0.01"), Decimal("0.02"), Decimal("0.03"), 30, 5)
    assert news_estimate.signed_shocks(NewsDirection.UP, band) == (
        Decimal("0.01"),
        Decimal("0.02"),
        Decimal("0.03"),
    )
    assert news_estimate.signed_shocks(NewsDirection.DOWN, band)[1] == Decimal("-0.02")
    low, mid, high = news_estimate.signed_shocks(NewsDirection.UNCERTAIN, band)
    assert (low, mid, high) == (Decimal("-0.02"), Decimal("0"), Decimal("0.02"))


def test_reaction_session_and_timing() -> None:
    after_close = datetime(2026, 11, 6, 22, 0, tzinfo=UTC)  # viernes, tras el cierre
    assert news_estimate.reaction_session(after_close) == date(2026, 11, 9)
    saturday = datetime(2026, 11, 7, 10, 0, tzinfo=UTC)
    assert news_estimate.reaction_session(saturday) == date(2026, 11, 9)
    timing, when = news_estimate.effect_timing(
        PriceKind.NAV_DAILY, AssetType.FUND, date(2026, 11, 6)
    )
    assert timing is EffectTiming.NEXT_NAV and when == datetime(2026, 11, 9, tzinfo=UTC)
    timing, when = news_estimate.effect_timing(
        PriceKind.INTRADAY, AssetType.STOCK, date(2026, 11, 6)
    )
    assert timing is EffectTiming.SAME_SESSION and when == datetime(2026, 11, 6, tzinfo=UTC)
    assert (
        news_estimate.effect_timing(PriceKind.NAV_DAILY, AssetType.DEPOSIT, date(2026, 11, 6))[0]
        is EffectTiming.NO_DAILY_PRICE
    )


def test_session_move() -> None:
    series = [(date(2026, 11, 4), Decimal("200")), (date(2026, 11, 5), Decimal("180"))]
    assert news_estimate.session_move(series, date(2026, 11, 5)) == Decimal("-0.10000")
    assert news_estimate.session_move(series, date(2026, 11, 6)) is None


# --- Ruta con la cartera de Laura ---


def _news(when: datetime, direction: str = "down", relevance: str = "high", n: int = 0) -> str:
    raw = RawNews(
        f"https://elmundo.es/nvidia-{n}",
        f"Nvidia noticia {n}",
        "",
        when,
        "El Mundo",
        "x",
        "es",
        "q",
    )
    [item_id] = repository.save_new([raw], when)
    classification: dict[str, Any] = {
        "category": "company",
        "relevance": relevance,
        "companies": [{"key": "NVDA", "name": "NVIDIA"}],
        "channels": [
            {
                "factor": None,
                "company_key": "NVDA",
                "direction": direction,
                "label": "NVIDIA",
                "rationale": "La noticia pesa sobre la acción.",
            },
            {
                "factor": "EQ_US_TECH",
                "company_key": None,
                "direction": direction,
                "label": "tecnológicas",
                "rationale": "NVIDIA pesa en las tecnológicas.",
            },
        ],
        "causal_chain": ["NVIDIA anuncia algo.", "Su acción reacciona."],
        "summary_es": "Una noticia sobre NVIDIA.",
    }
    repository.save_classification(item_id, classification, "test", when)
    return item_id


def test_closed_session_is_measured_with_the_real_move(client: TestClient) -> None:
    """El 5 nov NVIDIA cerró con fuerte caída en los CSV: el impacto medido es negativo."""
    clock.set_now(datetime(2026, 11, 6, 18, 0, tzinfo=UTC))
    news_id = _news(datetime(2026, 11, 5, 9, 0, tzinfo=UTC), direction="up")
    [item] = client.get(URL).json()
    estimate = item["estimate"]
    assert item["id"] == news_id
    assert estimate["status"] == "measured" and estimate["method"] == "measured"
    assert Decimal(estimate["impact_eur"]) < 0  # el dato manda, no la dirección del LLM
    assert estimate["horizon_sessions"] == 1
    nvda = next(p for p in estimate["positions"] if p["asset_id"] == NVDA)
    assert nvda["timing"] == "same_session"
    assert nvda["effective_from"] == "2026-11-05T00:00:00Z"
    assert NVDA in item["asset_ids"]
    trace = client.get(f"{API_PREFIX}/traces/{estimate['calc_id']}")
    assert trace.status_code == 200, trace.text


def test_open_session_is_estimated_and_only_the_sign_comes_from_the_classification(
    client: TestClient,
) -> None:
    clock.set_now(datetime(2026, 11, 6, 18, 0, tzinfo=UTC))
    down_id = _news(datetime(2026, 11, 6, 15, 0, tzinfo=UTC), direction="down", n=1)
    up_id = _news(datetime(2026, 11, 6, 16, 0, tzinfo=UTC), direction="up", n=2)
    items = {i["id"]: i["estimate"] for i in client.get(URL).json()}
    down, up = items[down_id], items[up_id]
    assert down["status"] == "estimated" and down["method"] == "volatility"
    assert down["horizon_sessions"] == 5 and down["analogs_count"] >= 20
    assert down["confidence"] != "alta"
    assert Decimal(down["low_eur"]) <= Decimal(down["impact_eur"]) <= Decimal(down["high_eur"])
    assert Decimal(down["impact_eur"]) < 0 < Decimal(up["impact_eur"])
    assert abs(Decimal(down["impact_eur"]) + Decimal(up["impact_eur"])) <= Decimal("1.00")
    fund = next(p for p in down["positions"] if p["timing"] == "next_nav")
    assert fund["effective_from"] == "2026-11-09T00:00:00Z"


def test_low_relevance_and_future_news_are_left_out(client: TestClient) -> None:
    clock.set_now(datetime(2026, 11, 6, 18, 0, tzinfo=UTC))
    low_id = _news(datetime(2026, 11, 5, 9, 0, tzinfo=UTC), relevance="low", n=3)
    _news(datetime(2026, 11, 8, 9, 0, tzinfo=UTC), n=4)  # después del reloj
    assert client.get(URL).json() == []
    everything = client.get(URL, params={"affecting": "false"}).json()
    assert [i["id"] for i in everything] == [low_id]
    assert everything[0]["estimate"]["status"] == "not_relevant"
    detail = client.get(f"{URL}/{low_id}").json()
    assert detail["estimate"]["status"] == "not_relevant"
    assert client.get(f"{URL}/news_missing").status_code == 404
