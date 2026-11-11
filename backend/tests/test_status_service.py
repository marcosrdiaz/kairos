"""Estado precalculado del widget: lectura sin modelo, `recompute`, traza y refresco (T2-04)."""

import subprocess
import sys
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.agents import claude
from app.core import clock, trace
from app.events import service as events_service
from app.main import API_PREFIX
from app.schemas.status import StatusOut
from app.status import config, service
from tests.fakes.claude_stream import FakeStreamingClaude, Reply

NOW = datetime(2026, 11, 8, 18, 0, tzinfo=UTC)
SENTENCE = "Tu cartera se mueve por un evento reciente. Toca para ver por qué."


class _Ticks:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def ticks(monkeypatch: pytest.MonkeyPatch) -> _Ticks:
    fake = _Ticks()
    monkeypatch.setattr(service, "_monotonic", fake)
    return fake


@pytest.fixture(autouse=True)
def _clean() -> Iterator[None]:
    clock.set_now(NOW)
    yield
    claude.set_client(None)


def _get(client: TestClient, portfolio_id: str = "laura") -> dict[str, Any]:
    response = client.get(f"{API_PREFIX}/portfolios/{portfolio_id}/status")
    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    return body


@pytest.mark.parametrize("module", ["app.agents.context", "app.status.service"])
def test_module_can_be_the_first_import(module: str) -> None:
    """`agents.context` usa `status` y `status` usa `agents`: el ciclo no debe romper nada."""
    done = subprocess.run([sys.executable, "-c", f"import {module}"], capture_output=True)
    assert done.returncode == 0, done.stderr.decode(errors="replace")


def test_laura_starts_tranquilo_with_real_figures(client: TestClient) -> None:
    body = _get(client)
    portfolio = client.get(f"{API_PREFIX}/portfolios/laura").json()
    assert body["state"] == "tranquilo"
    assert body["state_label"] == "Tranquilo"
    assert body["total_eur"] == portfolio["total_eur"]
    assert body["change_week_pct"] == portfolio["change_week_pct"]
    assert body["reason"] == {"kind": "none", "event_id": None, "event_impact_eur": None}
    assert body["computed_at"] == "2026-11-08T18:00:00Z"


def test_unknown_portfolio_is_404(client: TestClient) -> None:
    assert client.get(f"{API_PREFIX}/portfolios/nadie/status").status_code == 404


def test_recent_event_turns_it_atento_with_the_impact(client: TestClient) -> None:
    events_service.replay("nvda-2025-02")
    event = client.get(f"{API_PREFIX}/portfolios/laura/events").json()[0]
    body = _get(client)
    assert body["state"] == "atento"
    assert body["reason"] == {
        "kind": "event",
        "event_id": "nvda-2025-02",
        "event_impact_eur": event["impact_eur"],
    }


def test_preloaded_events_stay_tranquilo(client: TestClient) -> None:
    client.post(f"{API_PREFIX}/demo/reset", json={"preload": True})
    assert _get(client)["state"] == "tranquilo"


def test_drift_turns_it_revisa_plan(client: TestClient) -> None:
    body = {
        "target": {"equity": "0.30", "fixed_income": "0.60", "cash": "0.10"},
        "drift_threshold": "0.05",
    }
    assert client.put(f"{API_PREFIX}/portfolios/laura/plan", json=body).status_code == 200
    service.recompute("laura")
    status = _get(client)
    assert status["state"] == "revisa_plan"
    assert status["state_label"] == "Revisa tu plan"
    assert status["reason"]["kind"] == "drift"


def test_read_never_calls_the_model(client: TestClient) -> None:
    fake = FakeStreamingClaude()
    claude.set_client(fake)
    body = _get(client)
    assert fake.messages.calls == []
    assert body["sentence_status"] == "template"
    assert body["sentence"]


def test_recompute_writes_the_sentence_with_the_model(client: TestClient) -> None:
    claude.set_client(FakeStreamingClaude(Reply(SENTENCE)))
    out = service.recompute("laura")
    assert out.sentence == SENTENCE
    assert out.sentence_status == "ok"
    assert _get(client)["sentence"] == SENTENCE


def test_recompute_with_blocked_model_uses_a_validated_template(client: TestClient) -> None:
    claude.set_client(FakeStreamingClaude(Reply("Compra ya."), Reply("Vende todo.")))
    out = service.recompute("laura")
    assert out.sentence_status == "template"
    assert "ompra" not in out.sentence


def test_recompute_keeps_a_model_sentence_if_nothing_changed(client: TestClient) -> None:
    fake = FakeStreamingClaude(Reply(SENTENCE))
    claude.set_client(fake)
    first = service.recompute("laura")
    assert service.recompute("laura") == first
    assert len(fake.messages.calls) == 1


def test_calc_id_is_stable_between_reads(client: TestClient, ticks: _Ticks) -> None:
    first = _get(client)
    ticks.now += config.REFRESH_S - 1
    assert _get(client) == first
    ticks.now += config.REFRESH_S + 1
    assert _get(client) == first, "sin cambios, tampoco cambia al refrescar"


def test_operation_shows_up_after_the_refresh_interval(client: TestClient, ticks: _Ticks) -> None:
    first = _get(client)
    asset_id = client.get(f"{API_PREFIX}/portfolios/laura").json()["positions"][0]["asset_id"]
    body = {"type": "buy", "asset_id": asset_id, "amount_eur": "1000.00"}
    assert client.post(f"{API_PREFIX}/portfolios/laura/transactions", json=body).status_code < 300
    assert _get(client) == first
    ticks.now += config.REFRESH_S + 1
    second = _get(client)
    assert second["total_eur"] != first["total_eur"]
    assert second["calc_id"] != first["calc_id"]


def test_refresh_notices_the_72_hour_window_closing(client: TestClient, ticks: _Ticks) -> None:
    events_service.replay("nvda-2025-02")
    assert _get(client)["state"] == "atento"
    clock.set_now(NOW + timedelta(hours=73))
    ticks.now += config.REFRESH_S + 1
    assert _get(client)["state"] == "tranquilo"


def test_demo_reset_clears_the_state(client: TestClient) -> None:
    events_service.replay("nvda-2025-02")
    assert _get(client)["state"] == "atento"
    client.post(f"{API_PREFIX}/demo/reset")
    assert _get(client)["state"] == "tranquilo"


def test_every_figure_is_traceable_to_its_parents(client: TestClient) -> None:
    events_service.replay("nvda-2025-02")
    out = StatusOut.model_validate(_get(client))
    record = trace.get(out.calc_id)
    assert record is not None
    assert record.kind == "status"
    assert record.outputs["state"] == "atento"
    event_calc = client.get(f"{API_PREFIX}/portfolios/laura/events").json()[0]["calc_id"]
    assert event_calc in record.parent_calc_ids
    assert len(record.parent_calc_ids) == 3, "valoración, plan e impacto"


def test_price_as_of_ignores_fixed_value_assets(client: TestClient) -> None:
    """Javier tiene un depósito y un plan de pensiones de valor fijo, cuyo precio lleva la fecha del
    reloj: «Precios a» es la del último precio de mercado, no la de hoy."""
    portfolio = client.get(f"{API_PREFIX}/portfolios/javier").json()
    fixed = {"DEP-12M", "PP-MIXTO"}
    held = {p["asset_id"] for p in portfolio["positions"]}
    assert fixed <= held  # el caso existe en la cartera de ejemplo
    market = [p["price_at"] for p in portfolio["positions"] if p["asset_id"] not in fixed]
    status = _get(client, "javier")
    assert status["price_as_of"] == max(market)
    assert datetime.fromisoformat(status["price_as_of"]).date() < NOW.date()
