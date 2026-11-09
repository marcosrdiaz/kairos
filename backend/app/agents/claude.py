"""Cliente de Claude del explicador y de los textos de widget, avisos y eventos.

Sin `ANTHROPIC_API_KEY` no hay cliente (`get_client` devuelve `None`) y todo sale de plantilla
(decisión 13 del diseño del MVP). Los tests inyectan un cliente falso con `set_client`.
"""

from functools import cache
from pathlib import Path
from typing import Any

import anthropic
import httpx2  # el transporte del SDK: sus errores no se envuelven al iterar un stream

from app.config import get_settings

PROMPTS_DIR = Path(__file__).parent / "prompts"
PROMPT_PATH = PROMPTS_DIR / "explainer.md"
WRITER_PROMPT_PATH = PROMPTS_DIR / "writer.md"
TIMEOUT_S = 5.0
MAX_TOKENS = 2048
EFFORT = "low"
_NO_THINKING_PREFIX = "claude-haiku-5"
"""Modelos en los que se apaga el razonamiento (Haiku 5.5 lo admite con esfuerzo ≤ `high`)."""


class ModelOutputError(Exception):
    """El modelo ha respondido, pero sin nada utilizable (rechazo, texto vacío)."""


UPSTREAM_ERRORS: tuple[type[Exception], ...] = (
    anthropic.AnthropicError,
    httpx2.HTTPError,
    ModelOutputError,
)
"""Fallos que llevan a la plantilla: API caída o cortada a mitad, tiempo agotado, rechazo."""

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
    return _real_client(api_key)


@cache
def _real_client(api_key: str) -> anthropic.Anthropic:
    """Un cliente por clave: reutiliza las conexiones (sin un TLS nuevo en cada turno)."""
    return anthropic.Anthropic(api_key=api_key, timeout=TIMEOUT_S, max_retries=0)


@cache
def system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


@cache
def writer_prompt() -> str:
    return WRITER_PROMPT_PATH.read_text(encoding="utf-8")


def base_kwargs() -> dict[str, Any]:
    """Parámetros comunes. Modelo rápido (`ANTHROPIC_MODEL_FAST`) y esfuerzo bajo: son 2-3
    frases y la voz necesita la primera en menos de un segundo. En Haiku 5.5, sin razonamiento."""
    model = get_settings().anthropic_model_fast
    kwargs: dict[str, Any] = {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "output_config": {"effort": EFFORT},
    }
    if model.startswith(_NO_THINKING_PREFIX):
        kwargs["thinking"] = {"type": "disabled"}
    return kwargs


def final_text(message: Any) -> str:
    """Texto de un mensaje final. Un rechazo o un texto vacío cuentan como fallo del modelo."""
    if getattr(message, "stop_reason", None) == "refusal":
        raise ModelOutputError("el modelo ha rechazado la petición")
    parts = [block.text for block in message.content if getattr(block, "type", "") == "text"]
    text = " ".join(" ".join(parts).split())
    if not text:
        raise ModelOutputError("respuesta vacía")
    return text


def usage_of(message: Any) -> dict[str, int]:
    """Tokens de una respuesta, para comprobar que la caché del prompt se usa."""
    usage = getattr(message, "usage", None)
    keys = (
        "input_tokens",
        "output_tokens",
        "cache_read_input_tokens",
        "cache_creation_input_tokens",
    )
    return {key: int(getattr(usage, key, 0) or 0) for key in keys}
