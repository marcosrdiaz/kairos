"""Clasificador de noticias (T4-29): Claude lee titulares y devuelve categoría, empresas, canales
con su dirección, cadena causal, relevancia y un resumen en español. **Sin ninguna cifra**
(regla 1): la magnitud y el plazo los pone el motor de impacto con datos (T4-30).

Trabaja por lotes. La salida del modelo se valida noticia a noticia: una noticia con dígitos,
con una orden o un consejo (patrones del guardián) o con una empresa desconocida se descarta y
queda sin clasificar para la siguiente pasada; el resto del lote se guarda.
"""

import hashlib
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from functools import cache
from pathlib import Path
from typing import Any

import anthropic
from pydantic import BaseModel, ValidationError

from app.agents import guardian
from app.config import get_settings
from app.schemas.common import Factor
from app.schemas.events import CompanyRef, Relevance
from app.schemas.news import NewsCategory, NewsChannel, NewsDirection

PROMPT_PATH = Path(__file__).parent / "prompts" / "news_classifier.md"
BATCH_SIZE = 20
_MAX_TOKENS = 8000
_TIMEOUT_S = 90.0
_DIGIT = re.compile(r"\d")
_MAX_CHANNELS = 3


@dataclass(frozen=True)
class NewsInput:
    index: int
    title: str
    summary: str
    source: str
    published_at: datetime


class ChannelDraft(BaseModel):
    factor: str | None = None
    company_key: str | None = None
    direction: str
    label: str
    rationale: str


class ItemDraft(BaseModel):
    """Lo que devuelve el modelo por noticia, sin validar todavía (se valida en `_accept`)."""

    index: int
    category: str
    relevance: str
    companies: list[str]
    channels: list[ChannelDraft]
    causal_chain: list[str]
    summary_es: str


class BatchDraft(BaseModel):
    items: list[ItemDraft]


class NewsClassification(BaseModel):
    """Clasificación validada que se guarda en `news_item.classification`."""

    category: NewsCategory
    relevance: Relevance
    companies: list[CompanyRef]
    channels: list[NewsChannel]
    causal_chain: list[str]
    summary_es: str


class ClassifierError(Exception):
    """Sin cliente de Claude o sin respuesta utilizable."""


@cache
def _prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def classifier_key() -> str:
    """Versión del prompt y modelo: si cambia, las noticias se vuelven a clasificar."""
    model = get_settings().anthropic_model_fast
    digest = hashlib.sha256(f"{_prompt()}|{model}".encode()).hexdigest()[:16]
    return f"nc1-{digest}"


def _user_message(items: Sequence[NewsInput], companies: Mapping[str, str]) -> str:
    known = "\n".join(f"- `{key}`: {name}" for key, name in sorted(companies.items()))
    lines = [f"Empresas disponibles:\n{known}", "", "<noticias>"]
    for item in items:
        day = item.published_at.date().isoformat()
        lines.append(f"[{item.index}] ({item.source}, {day}) {item.title}")
        if item.summary:
            lines.append(f"    Resumen: {item.summary}")
    lines.append("</noticias>")
    return "\n".join(lines)


def _clean_texts(draft: ItemDraft) -> list[str]:
    return [
        draft.summary_es,
        *draft.causal_chain,
        *(c.label for c in draft.channels),
        *(c.rationale for c in draft.channels),
    ]


def _accept(draft: ItemDraft, companies: Mapping[str, str]) -> NewsClassification | None:
    """La clasificación validada, o `None` si no se puede usar."""
    texts = _clean_texts(draft)
    if any(_DIGIT.search(t) for t in texts) or any(guardian.find_forbidden(t) for t in texts):
        return None
    keys = [key for key in dict.fromkeys(draft.companies) if key in companies]
    try:
        relevance = Relevance(draft.relevance)
        channels: list[NewsChannel] = []
        if relevance is not Relevance.LOW:
            for c in draft.channels[:_MAX_CHANNELS]:
                if c.company_key is not None and c.company_key not in keys:
                    continue
                channels.append(
                    NewsChannel(
                        factor=Factor(c.factor) if c.factor else None,
                        company_key=c.company_key,
                        direction=NewsDirection(c.direction),
                        label=c.label,
                        rationale=c.rationale,
                    )
                )
        return NewsClassification(
            category=NewsCategory(draft.category),
            relevance=relevance,
            companies=[CompanyRef(key=key, name=companies[key]) for key in keys],
            channels=channels,
            causal_chain=[step for step in draft.causal_chain if step.strip()],
            summary_es=draft.summary_es.strip(),
        )
    except (ValueError, ValidationError):
        return None


_test_client: Any | None = None


def set_client(client: Any | None) -> None:
    """Sustituye el cliente de Claude (tests). `None` vuelve al real."""
    global _test_client
    _test_client = client


def _client() -> Any:
    if _test_client is not None:
        return _test_client
    api_key = get_settings().anthropic_api_key
    if not api_key:
        raise ClassifierError("Falta ANTHROPIC_API_KEY")
    return anthropic.Anthropic(api_key=api_key, timeout=_TIMEOUT_S, max_retries=1)


def classify(
    items: Sequence[NewsInput], companies: Mapping[str, str]
) -> dict[int, NewsClassification]:
    """Clasifica un lote (como mucho `BATCH_SIZE`). Devuelve las aceptadas por `index`.
    `ClassifierError` si no hay cliente o el modelo no responde nada utilizable."""
    if not items:
        return {}
    client = _client()
    try:
        response = client.messages.parse(
            model=get_settings().anthropic_model_fast,
            max_tokens=_MAX_TOKENS,
            system=_prompt(),
            messages=[{"role": "user", "content": _user_message(items, companies)}],
            output_format=BatchDraft,
        )
    except (anthropic.AnthropicError, ValidationError) as error:
        raise ClassifierError(str(error) or type(error).__name__) from error
    batch = response.parsed_output
    if response.stop_reason == "refusal" or batch is None:
        raise ClassifierError(f"sin resultado ({response.stop_reason})")
    wanted = {item.index for item in items}
    accepted: dict[int, NewsClassification] = {}
    for draft in batch.items:
        if draft.index in wanted and draft.index not in accepted:
            result = _accept(draft, companies)
            if result is not None:
                accepted[draft.index] = result
    return accepted
