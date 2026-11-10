"""GDELT DOC 2.0 (https://api.gdeltproject.org/api/v2/doc/doc): índice abierto de noticias, sin
clave, con búsqueda por fechas. Fuente opcional (`--gdelt`): limita a **una petición cada 5 s**
y a veces responde 429 durante un rato.

GDELT no da resumen: solo titular, URL, medio, idioma y fecha. Solo cuentan los medios de
`sources.TRUSTED_DOMAINS`. Funciones puras: sin red ni BD.
"""

import json
from datetime import UTC, datetime
from urllib.parse import urlencode

from app.news.ingest.sources import RawNews, clean_text, trusted_source

API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
MAX_RECORDS = 250
MIN_INTERVAL_S = 5.5

_LANGUAGES = {"english": "en", "spanish": "es"}


def query_url(query: str, language: str, start: datetime, end: datetime) -> str:
    """URL de búsqueda de `query` en `language` (`en` o `es`) entre `start` y `end` (UTC)."""
    lang = "english" if language == "en" else "spanish"
    params = {
        "query": f"{query} sourcelang:{lang}",
        "mode": "artlist",
        "format": "json",
        "maxrecords": str(MAX_RECORDS),
        "sort": "hybridrel",
        "startdatetime": start.astimezone(UTC).strftime("%Y%m%d%H%M%S"),
        "enddatetime": end.astimezone(UTC).strftime("%Y%m%d%H%M%S"),
    }
    return f"{API_URL}?{urlencode(params)}"


def parse(text: str, query: str) -> list[RawNews]:
    """Noticias de medios de confianza de la respuesta. `ValueError` si no es JSON (GDELT
    responde con texto plano cuando se supera su límite de peticiones)."""
    try:
        data = json.loads(text) if text.strip() else {}
    except json.JSONDecodeError as error:
        raise ValueError(f"GDELT no ha devuelto JSON: {text[:120]!r}") from error
    items: list[RawNews] = []
    for article in data.get("articles", []):
        name = trusted_source(str(article.get("domain", "")))
        language = _LANGUAGES.get(str(article.get("language", "")).lower())
        url = str(article.get("url", "")).strip()
        title = clean_text(str(article.get("title", "")))
        if not name or not language or not url or not title:
            continue
        try:
            seen = str(article["seendate"]).replace("Z", "+0000")
            published = datetime.strptime(seen, "%Y%m%dT%H%M%S%z")
        except (KeyError, ValueError):
            continue
        items.append(
            RawNews(
                url=url,
                title=title,
                summary="",
                published_at=published.astimezone(UTC),
                source_name=name,
                provider="gdelt",
                language=language,
                query=query,
            )
        )
    return items
