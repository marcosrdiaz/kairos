"""Cliente de Claude del explicador y de los textos de widget, avisos y eventos.

Sin `ANTHROPIC_API_KEY` no hay cliente (`get_client` devuelve `None`) y todo sale de plantilla
(decisión 13 del diseño del MVP). Los tests inyectan un cliente falso con `set_client`.
"""

from functools import cache
from pathlib import Path
from typing import Any

import anthropic

from app.config import get_settings

PROMPT_PATH = Path(__file__).parent / "prompts" / "explainer.md"
TIMEOUT_S = 8.0
MAX_TOKENS = 2048
EFFORT = "low"
UPSTREAM_ERRORS: tuple[type[Exception], ...] = (anthropic.AnthropicError, ValueError)
"""Fallos que llevan a la plantilla: API caída, tiempo agotado, respuesta ilegible."""

_client: Any | None = None


def set_client(client: Any | None) -> None:
    """Sustituye el cliente (tests). `None` vuelve al real, según la clave del `.env`."""
    global _client
    _client = client


def get_client() -> Any | None:
    if _client is not None:
        return _client
    api_key = get_settings().anthropic_api_key
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key, timeout=TIMEOUT_S, max_retries=0)


@cache
def system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def base_kwargs() -> dict[str, Any]:
    """Parámetros comunes. Modelo rápido (`ANTHROPIC_MODEL_FAST`) y esfuerzo bajo: son 2-3
    frases y la voz necesita la primera en menos de un segundo."""
    return {
        "model": get_settings().anthropic_model_fast,
        "max_tokens": MAX_TOKENS,
        "output_config": {"effort": EFFORT},
    }


def final_text(message: Any) -> str:
    """Texto de un mensaje final. Un rechazo cuenta como fallo del modelo."""
    if getattr(message, "stop_reason", None) == "refusal":
        raise ValueError("el modelo ha rechazado la petición")
    parts = [block.text for block in message.content if getattr(block, "type", "") == "text"]
    return " ".join(" ".join(parts).split())
