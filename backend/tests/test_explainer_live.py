"""Las 3 preguntas tipo contra Claude real (criterio de hecho de T1-17).

No corre en CI (`-m 'not live'` por defecto). La clave se toma del entorno o, si no está, del
`.env` de la raíz del repo (no del directorio desde el que se lanza pytest). Desde `backend/`:

    pytest -m live tests/test_explainer_live.py -s

Imprime los eventos SSE de cada pregunta y el uso de tokens de cada llamada, incluidos
`cache_read_input_tokens` y `cache_creation_input_tokens`, para ver si la caché del prompt se usa.
"""

import json
import logging
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

REPO_ENV = Path(__file__).resolve().parents[2] / ".env"
QUESTIONS = ["¿Por qué ha bajado?", "¿Me afecta lo del BCE?", "¿Voy bien?"]


def _api_key() -> str:
    """Primero el entorno; si no, el `.env` de la raíz del repo. Nunca se imprime."""
    from_env = os.environ.get("ANTHROPIC_API_KEY", "")
    if from_env:
        return from_env
    if not REPO_ENV.is_file():
        return ""
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
def _real_claude(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> Iterator[None]:
    monkeypatch.setenv("ANTHROPIC_API_KEY", _API_KEY)
    get_settings.cache_clear()
    claude.set_client(None)
    context.invalidate()
    voice_service.reset()
    caplog.set_level(logging.INFO, logger="app.agents.explainer")
    yield
    context.invalidate()


def _ask(client: TestClient, question: str, channel: str) -> list[dict[str, Any]]:
    body = {"question": question, "channel": channel, "session_id": "ses_live"}
    response = client.post(f"{API_PREFIX}/portfolios/laura/ask", json=body)
    assert response.status_code == 200
    return [json.loads(f.removeprefix("data: ")) for f in response.text.split("\n\n") if f]


def _usage(caplog: pytest.LogCaptureFixture) -> list[dict[str, int]]:
    """Uso de tokens que el explicador registra tras cada llamada (`Turn._record_usage`)."""
    records = [r for r in caplog.records if "uso de Claude" in r.getMessage()]
    usage: list[dict[str, int]] = []
    for record in records:
        if isinstance(record.args, tuple) and isinstance(record.args[1], dict):
            usage.append(record.args[1])
    return usage


@pytest.mark.parametrize("channel", ["voice", "text"])
@pytest.mark.parametrize("question", QUESTIONS)
def test_demo_questions_with_real_claude(
    client: TestClient, caplog: pytest.LogCaptureFixture, question: str, channel: str
) -> None:
    assert client.post(f"{API_PREFIX}/demo/replay/bce-2025-06").status_code == 200
    context.invalidate()
    caplog.clear()
    events = _ask(client, question, channel)
    print(question, json.dumps(events, ensure_ascii=False, indent=1))
    print("uso:", _usage(caplog))
    done = events[-1]
    assert done["type"] == "done", done
    sentences = [e for e in events if e["type"] == "sentence"]
    assert sentences
    assert any(s["calc_ids"] for s in sentences)
    if channel == "voice":
        assert len(sentences) <= 3
    assert done["fallback_used"] is False, "Claude real no debería acabar en plantilla"


def test_prompt_cache_is_used_on_the_second_turn(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    """Dos turnos seguidos con el mismo contexto: el segundo debería leer de la caché. Solo se
    imprime: si el prefijo no llega al mínimo cacheable del modelo, la caché no se activa."""
    _ask(client, QUESTIONS[2], "text")
    caplog.clear()
    events = _ask(client, QUESTIONS[2], "text")
    usage = _usage(caplog)
    print("uso del segundo turno:", usage)
    assert events[-1]["type"] == "done"
    assert usage, "el explicador debe registrar el uso de cada llamada"
