"""Pipeline de replay (diseño del MVP §2): `build_shockset`, respaldo, orden y control de demo."""

import json
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.agents import analyzer
from app.agents.analyzer import AnalyzerDraft
from app.alerts import service as alerts_service
from app.core import clock
from app.core.db import session_scope
from app.events import pipeline, service
from app.events.models import Event
from app.main import API_PREFIX
from app.schemas.common import Factor
from app.schemas.events import (
    Channel,
    CompanyRef,
    Direction,
    EventAnalysis,
    EventIn,
    EventType,
    Relevance,
    ReplayRequest,
    SelectedBy,
)
from app.status import service as status_service
from tests.fakes.claude import FakeClaude

REPLAY_DIR = Path(__file__).resolve().parents[2] / "data" / "events" / "replay"
NOW = datetime(2026, 11, 8, 18, 0, tzinfo=UTC)
EQ = Factor.EQ_GLOBAL
RATES = Factor.RATES_EUR


def _event(event_id: str) -> EventIn:
    data = json.loads((REPLAY_DIR / f"{event_id}.json").read_text(encoding="utf-8"))
    return EventIn.model_validate(data)


def _channel(factor: Factor) -> Channel:
    return Channel(factor=factor, direction=Direction.UP, label="etiqueta", rationale="Motivo")


def _analysis(
    event: EventIn, factors: list[Factor], companies: list[str] | None = None
) -> EventAnalysis:
    return EventAnalysis(
        schema_version=1,
        event_id=event.id,
        event_type=event.type,
        entities=[],
        channels=[_channel(f) for f in factors],
        companies=[CompanyRef(key=c, name="Empresa") for c in companies or []],
        causal_chain=["Cadena"],
        relevance=Relevance.HIGH,
        analyzed_model="fake",
        fallback=False,
    )


def _draft(factors: list[Factor]) -> AnalyzerDraft:
    return AnalyzerDraft(
        event_type=EventType.MACRO,
        entities=[],
        channels=[_channel(f) for f in factors],
        companies=[],
        causal_chain=["Pasa algo", "Y luego otra cosa"],
        relevance=Relevance.HIGH,
    )


@pytest.fixture(autouse=True)
def _reset_client() -> Iterator[None]:
    clock.set_now(NOW)
    yield
    analyzer.set_client(None)


# --- build_shockset ---


def test_shockset_uses_every_observed_factor_whatever_the_analyzer_chose() -> None:
    # D-083: los canales del analizador solo son narrativa; nunca cambian una cifra.
    event = _event("bce-2025-06")
    assert event.observed is not None
    shocks = pipeline.build_shockset(_analysis(event, [RATES]), event)
    assert shocks.factor_shocks == event.observed.factors
    assert shocks.company_moves == {}
    assert shocks.selected_by is SelectedBy.ALL_OBSERVED
    assert shocks.source.ref == "bce-2025-06"
    assert "jun 2025" in shocks.source.label


def test_shockset_ignores_companies_not_observed() -> None:
    event = _event("bce-2025-06")
    shocks = pipeline.build_shockset(_analysis(event, [RATES], ["NVDA"]), event)
    assert shocks.company_moves == {}


def test_shockset_keeps_every_observed_company_move() -> None:
    event = _event("nvda-2025-02")
    assert event.observed is not None
    for companies in (["NVDA"], []):
        shocks = pipeline.build_shockset(_analysis(event, [EQ], companies), event)
        assert shocks.company_moves == event.observed.companies
        assert shocks.selected_by is SelectedBy.ALL_OBSERVED


def test_empty_selection_uses_everything_observed() -> None:
    event = _event("bce-2025-06")
    assert event.observed is not None
    shocks = pipeline.build_shockset(_analysis(event, []), event)
    assert shocks.factor_shocks == event.observed.factors
    assert shocks.selected_by is SelectedBy.ALL_OBSERVED


def test_fallback_analysis_uses_the_human_chain_and_all_factors() -> None:
    event = _event("oil-2025-06")
    assert event.observed is not None
    analysis = pipeline.fallback_analysis(event)
    assert analysis.fallback is True
    assert analysis.causal_chain == event.fallback_chain
    assert {c.factor for c in analysis.channels} == set(event.observed.factors)
    labels = {c.factor: c.label for c in analysis.channels}
    assert labels[Factor.OIL] == "petróleo"
    directions = {c.factor: c.direction for c in analysis.channels}
    assert directions[Factor.OIL] is Direction.UP
    assert directions[EQ] is Direction.DOWN
    shocks = pipeline.build_shockset(analysis, event)
    assert shocks.selected_by is SelectedBy.ALL_OBSERVED
    assert shocks.factor_shocks == event.observed.factors


def test_fallback_analysis_includes_companies() -> None:
    assert [c.key for c in pipeline.fallback_analysis(_event("nvda-2025-02")).companies] == ["NVDA"]


# --- Pipeline ---


def test_replay_falls_back_without_analyzer_and_shows_real_impacts(client: TestClient) -> None:
    response = client.post(f"{API_PREFIX}/demo/replay/oil-2025-06")
    assert response.status_code == 200
    body = response.json()
    assert set(body["portfolios"]) == {"laura", "javier"}
    assert body["elapsed_ms"] >= 0
    events = client.get(f"{API_PREFIX}/portfolios/laura/events", params={"days": 1}).json()
    assert [e["event_id"] for e in events] == ["oil-2025-06"]
    assert events[0]["calc_id"] == body["portfolios"]["laura"]
    assert events[0]["causal_chain"][:-1] == _event("oil-2025-06").fallback_chain
    assert events[0]["explanation_status"] == "template"
    assert events[0]["explanation"]


def test_replay_saves_event_with_analysis(client: TestClient) -> None:
    analyzer.set_client(FakeClaude(_draft([EQ])))
    client.post(f"{API_PREFIX}/demo/replay/oil-2025-06")
    with session_scope() as session:
        row = session.get(Event, "oil-2025-06")
        assert row is not None
        assert row.replay is True
        assert row.analysis is not None
        assert row.analysis["causal_chain"] == ["Pasa algo", "Y luego otra cosa"]
        assert row.analyzed_model == "claude-sonnet-5-5"


def _figures(client: TestClient) -> tuple[str, str, str]:
    event = client.get(f"{API_PREFIX}/portfolios/laura/events").json()[0]
    return event["impact_eur"], event["low_eur"], event["high_eur"]


def test_figures_are_the_same_with_and_without_the_analyzer(client: TestClient) -> None:
    # D-083: el analizador solo redacta. Sin él (respaldo) y con un análisis que solo elige la
    # bolsa, el impacto y el rango son idénticos.
    client.post(f"{API_PREFIX}/demo/replay/oil-2025-06")
    without = _figures(client)

    analyzer.set_client(FakeClaude(_draft([EQ])))
    client.post(f"{API_PREFIX}/demo/replay/oil-2025-06")
    event = client.get(f"{API_PREFIX}/portfolios/laura/events").json()[0]

    assert event["causal_chain"][:2] == ["Pasa algo", "Y luego otra cosa"]
    assert _figures(client) == without


# --- Caché del análisis (T2-26) ---


def test_replaying_again_reuses_the_cached_analysis(client: TestClient) -> None:
    fake = FakeClaude(_draft([EQ]))  # una sola respuesta: una segunda llamada fallaría
    analyzer.set_client(fake)
    client.post(f"{API_PREFIX}/demo/replay/oil-2025-06")
    client.post(f"{API_PREFIX}/demo/replay/oil-2025-06")

    assert len(fake.messages.calls) == 1
    event = client.get(f"{API_PREFIX}/portfolios/laura/events").json()[0]
    assert event["causal_chain"][:2] == ["Pasa algo", "Y luego otra cosa"]


def test_the_cache_survives_demo_reset(client: TestClient) -> None:
    fake = FakeClaude(_draft([EQ]))
    analyzer.set_client(fake)
    client.post(f"{API_PREFIX}/demo/replay/oil-2025-06")
    assert client.post(f"{API_PREFIX}/demo/reset").status_code == 200

    client.post(f"{API_PREFIX}/demo/replay/oil-2025-06")

    assert len(fake.messages.calls) == 1


def test_fallback_is_not_cached(client: TestClient) -> None:
    client.post(f"{API_PREFIX}/demo/replay/oil-2025-06")  # sin clave: respaldo
    fake = FakeClaude(_draft([EQ]))
    analyzer.set_client(fake)

    client.post(f"{API_PREFIX}/demo/replay/oil-2025-06")

    assert len(fake.messages.calls) == 1


def test_a_new_prompt_invalidates_the_cache(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeClaude(_draft([EQ]), _draft([EQ]))
    analyzer.set_client(fake)
    client.post(f"{API_PREFIX}/demo/replay/oil-2025-06")
    monkeypatch.setattr(analyzer, "prompt_version", lambda: "otraversion0")

    client.post(f"{API_PREFIX}/demo/replay/oil-2025-06")

    assert len(fake.messages.calls) == 2


def test_preanalyze_fills_the_cache_for_the_replay(client: TestClient) -> None:
    fake = FakeClaude(_draft([EQ]))
    analyzer.set_client(fake)

    assert service.preanalyze(["oil-2025-06"]) == {"oil-2025-06": True}
    client.post(f"{API_PREFIX}/demo/replay/oil-2025-06")

    assert len(fake.messages.calls) == 1


def test_preanalyze_without_key_reports_fallback(client: TestClient) -> None:
    assert service.preanalyze(["bce-2025-06"]) == {"bce-2025-06": False}


def test_occurred_at_defaults_to_now(client: TestClient) -> None:
    client.post(f"{API_PREFIX}/demo/replay/oil-2025-06")
    event = client.get(f"{API_PREFIX}/portfolios/laura/events").json()[0]
    assert event["occurred_at"] == "2026-11-08T18:00:00Z"
    assert service.get_event("oil-2025-06").occurred_at == NOW


def test_occurred_at_from_body(client: TestClient) -> None:
    client.post(
        f"{API_PREFIX}/demo/replay/oil-2025-06", json={"occurred_at": "2026-11-04T18:00:00Z"}
    )
    event = client.get(f"{API_PREFIX}/portfolios/laura/events").json()[0]
    assert event["occurred_at"] == "2026-11-04T18:00:00Z"


def test_get_event_without_row_keeps_json_date(client: TestClient) -> None:
    assert service.get_event("oil-2025-06").occurred_at == _event("oil-2025-06").occurred_at


def test_shock_date_is_the_real_event_date(client: TestClient) -> None:
    client.post(f"{API_PREFIX}/demo/replay/oil-2025-06")
    source = client.get(f"{API_PREFIX}/portfolios/laura/events").json()[0]["sources"][0]
    assert source["as_of"] == "2025-06-13T00:00:00Z"


def _spy_alerts(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str]]:
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(alerts_service, "evaluate", lambda p, e: calls.append((p, e)))
    return calls


def test_silent_replay_generates_no_alerts(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _spy_alerts(monkeypatch)
    service.replay("oil-2025-06", ReplayRequest(silent=True))
    assert calls == []


def test_replay_evaluates_alerts_and_status_per_portfolio(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _spy_alerts(monkeypatch)
    recomputed: list[str] = []
    real = status_service.recompute

    def spy(portfolio_id: str) -> Any:
        recomputed.append(portfolio_id)
        return real(portfolio_id)

    monkeypatch.setattr(status_service, "recompute", spy)
    service.replay("oil-2025-06")
    assert calls == [("laura", "oil-2025-06"), ("javier", "oil-2025-06")]
    assert recomputed == ["laura", "javier"]


def test_replay_twice_replaces_the_impact(client: TestClient) -> None:
    client.post(f"{API_PREFIX}/demo/replay/oil-2025-06")
    second = client.post(f"{API_PREFIX}/demo/replay/oil-2025-06").json()
    events = client.get(f"{API_PREFIX}/portfolios/laura/events").json()
    assert [e["calc_id"] for e in events] == [second["portfolios"]["laura"]]


def test_unknown_event_is_404(client: TestClient) -> None:
    response = client.post(f"{API_PREFIX}/demo/replay/nada")
    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_event_id_cannot_escape_the_replay_directory(client: TestClient) -> None:
    assert client.post(f"{API_PREFIX}/demo/replay/..%2Fagenda").status_code == 404


# --- Reset y precarga ---


def test_demo_reset_removes_events_and_impacts(client: TestClient) -> None:
    client.post(f"{API_PREFIX}/demo/replay/oil-2025-06")
    client.post(f"{API_PREFIX}/demo/reset")
    assert client.get(f"{API_PREFIX}/portfolios/laura/events").json() == []
    with session_scope() as session:
        assert session.get(Event, "oil-2025-06") is None


def test_preload_replays_bce_and_oil_four_days_ago_silently(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _spy_alerts(monkeypatch)
    body = client.post(f"{API_PREFIX}/demo/reset", json={"preload": True}).json()
    assert body["preloaded_event_ids"] == ["bce-2025-06", "oil-2025-06"]
    assert calls == []
    events = client.get(f"{API_PREFIX}/portfolios/laura/events", params={"days": 7}).json()
    assert {e["event_id"] for e in events} == {"bce-2025-06", "oil-2025-06"}
    expected = (NOW - timedelta(hours=96)).isoformat().replace("+00:00", "Z")
    assert {e["occurred_at"] for e in events} == {expected}
