"""Las 40 preguntas de la evaluación (T3-01, T3-10) contra Claude real, en proceso (sin `make up`).

No corre en CI (`-m 'not live'` por defecto). Escribe el informe en `tests/eval/resultados.md`
y falla si alguna respuesta contiene una orden de compraventa, repite frases, mete relleno o no
termina bien. Desde `backend/`:

    uv run pytest -m live tests/eval/test_eval_live.py -s

Estado del guion: el replay de NVIDIA (paso 3) y el del BCE, como en la demo.
"""

import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.agents import claude, context
from app.config import Settings, get_settings
from app.main import API_PREFIX
from app.voice import service as voice_service
from tests.eval import load_script

ev = load_script()
REPO_ENV = Path(__file__).resolve().parents[3] / ".env"


def _api_key() -> str:
    """Primero el entorno; si no, el `.env` de la raíz del repo. Nunca se imprime."""
    from_env = os.environ.get("ANTHROPIC_API_KEY", "")
    if from_env or not REPO_ENV.is_file():
        return from_env
    return Settings(_env_file=REPO_ENV).anthropic_api_key


# Se lee al importar: el fixture común de `conftest.py` vacía la variable antes de cada test.
_API_KEY = _api_key()

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
    voice_service.reset()
    yield
    context.invalidate()


def test_all_questions_with_real_claude(client: TestClient) -> None:
    for event_id in ("bce-2025-06", "nvda-2025-02"):
        assert client.post(f"{API_PREFIX}/demo/replay/{event_id}").status_code == 200
    context.invalidate()

    def post(portfolio: str, body: dict[str, Any]) -> list[dict[str, Any]]:
        response = client.post(f"{API_PREFIX}/portfolios/{portfolio}/ask", json=body)
        assert response.status_code == 200
        events: list[dict[str, Any]] = ev.parse_sse(response.text)
        return events

    results = ev.evaluate(ev.load_questions(), post)
    header = (
        f"Claude real (`{get_settings().anthropic_model_fast}`), en proceso con "
        "`pytest -m live tests/eval/test_eval_live.py`, canal `text`, tras el replay del BCE y de "
        "NVIDIA sobre el seed."
    )
    ev.REPORT_FILE.write_text(ev.render_report(results, header), encoding="utf-8")
    summary = ev.summarize(results)
    print(summary, f"\nInforme: {ev.REPORT_FILE}")
    assert summary["errors"] == 0, [r.error for r in results if r.error]
    assert summary["orders"] == 0, [(r.q.id, r.orders, r.answer) for r in results if r.orders]
    assert summary["repeats"] == 0, [(r.q.id, r.repeats) for r in results if r.repeats]
    assert summary["filler"] == 0, [(r.q.id, r.filler) for r in results if r.filler]
