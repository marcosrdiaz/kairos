"""Las 3 preguntas tipo contra Claude real (criterio de hecho de T1-17).

No corre en CI (`-m 'not live'` por defecto). Para lanzarlo, con la clave en `backend/.env` o en
el entorno: `pytest -m live tests/test_explainer_live.py -s`.
"""

import json
import os
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.agents import claude, context
from app.config import Settings, get_settings
from app.main import API_PREFIX
from app.voice import service as voice_service

# Se lee al importar: el fixture común de `conftest.py` vacía la variable antes de cada test.
_API_KEY = os.environ.get("ANTHROPIC_API_KEY") or Settings().anthropic_api_key

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not _API_KEY, reason="sin ANTHROPIC_API_KEY"),
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


def _ask(client: TestClient, question: str, channel: str) -> list[dict[str, Any]]:
    body = {"question": question, "channel": channel, "session_id": "ses_live"}
    response = client.post(f"{API_PREFIX}/portfolios/laura/ask", json=body)
    assert response.status_code == 200
    return [json.loads(f.removeprefix("data: ")) for f in response.text.split("\n\n") if f]


@pytest.mark.parametrize("channel", ["voice", "text"])
@pytest.mark.parametrize(
    "question", ["¿Por qué ha bajado?", "¿Me afecta lo del BCE?", "¿Voy bien?"]
)
def test_demo_questions_with_real_claude(client: TestClient, question: str, channel: str) -> None:
    assert client.post(f"{API_PREFIX}/demo/replay/bce-2025-06").status_code == 200
    context.invalidate()
    events = _ask(client, question, channel)
    print(question, json.dumps(events, ensure_ascii=False, indent=1))
    done = events[-1]
    assert done["type"] == "done", done
    sentences = [e for e in events if e["type"] == "sentence"]
    assert sentences
    assert any(s["calc_ids"] for s in sentences)
    if channel == "voice":
        assert len(sentences) <= 3
    assert done["fallback_used"] is False, "Claude real no debería acabar en plantilla"
