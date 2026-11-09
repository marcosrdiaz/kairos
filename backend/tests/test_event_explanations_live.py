"""Criterio de T2-09 con Claude real: `explanation_status: ok` en 3 eventos × 2 carteras.

No corre en CI (`-m 'not live'` por defecto). La clave se busca como en `test_explainer_live.py`.
Desde `backend/`:

    pytest -m live tests/test_event_explanations_live.py -s
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.agents import claude, context
from app.config import get_settings
from app.main import API_PREFIX
from tests.test_explainer_live import _API_KEY, REPO_ENV

EVENT_IDS = ("bce-2025-06", "oil-2025-06", "nvda-2025-02")
PORTFOLIO_IDS = ("laura", "javier")

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        not _API_KEY, reason=f"sin ANTHROPIC_API_KEY (ni en el entorno ni en {REPO_ENV})"
    ),
]


@pytest.fixture(autouse=True)
def _real_claude(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("ANTHROPIC_API_KEY", _API_KEY)
    get_settings.cache_clear()
    claude.set_client(None)
    context.invalidate()
    yield
    claude.set_client(None)
    context.invalidate()


@pytest.mark.parametrize("event_id", EVENT_IDS)
def test_real_claude_explains_the_event_for_each_portfolio(
    client: TestClient, event_id: str
) -> None:
    assert client.post(f"{API_PREFIX}/demo/replay/{event_id}").status_code == 200
    for portfolio_id in PORTFOLIO_IDS:
        event = client.get(f"{API_PREFIX}/portfolios/{portfolio_id}/events").json()[0]
        print(event_id, portfolio_id, event["explanation_status"], event["explanation"])
        assert event["event_id"] == event_id
        assert event["explanation_status"] == "ok", event["explanation"]
