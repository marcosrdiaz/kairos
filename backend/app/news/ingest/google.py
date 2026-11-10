"""RSS de búsqueda de Google Noticias (edición España): titulares con fecha y medio, y búsqueda
por rango de fechas (`after:` / `before:`), así que sirve para cargar el histórico.

Solo se guarda lo que el propio RSS publica: titular, medio, fecha y enlace (el de Google
Noticias, que redirige al artículo). No se descarga el artículo. Solo cuentan los medios de
`sources.TRUSTED_DOMAINS`. Funciones puras: sin red ni BD.
"""

import xml.etree.ElementTree as ET
from datetime import UTC, date, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus, urlsplit

from app.news.ingest.sources import RawNews, clean_text, trusted_source

SEARCH_URL = "https://news.google.com/rss/search?q={q}&hl=es&gl=ES&ceid=ES:es"
MIN_INTERVAL_S = 1.5


def search_url(search: str, start: date, end: date) -> str:
    """Búsqueda de `search` publicada entre `start` y `end` (los dos incluidos)."""
    query = f"{search} after:{start.isoformat()} before:{(end + timedelta(days=1)).isoformat()}"
    return SEARCH_URL.format(q=quote_plus(query))


def _strip_source(title: str, source: str) -> str:
    """Google añade « - Medio» al final del titular."""
    suffix = f" - {source}"
    return title[: -len(suffix)].rstrip() if source and title.endswith(suffix) else title


def parse(xml_text: str, query: str) -> list[RawNews]:
    """Entradas de medios de confianza con titular, enlace y fecha válidos."""
    root = ET.fromstring(xml_text)
    items: list[RawNews] = []
    for item in root.iter("item"):
        source = item.find("source")
        source_url = source.get("url", "") if source is not None else ""
        name = trusted_source(urlsplit(source_url).netloc)
        link = (item.findtext("link") or "").strip()
        raw_title = clean_text(item.findtext("title") or "")
        raw_date = (item.findtext("pubDate") or "").strip()
        if not name or not link or not raw_title or not raw_date:
            continue
        try:
            published = parsedate_to_datetime(raw_date)
        except (TypeError, ValueError):
            continue
        if published.tzinfo is None:
            continue
        source_text = clean_text(source.text or "") if source is not None else ""
        items.append(
            RawNews(
                url=link,
                title=_strip_source(raw_title, source_text),
                summary="",
                published_at=published.astimezone(UTC),
                source_name=name,
                provider="google_rss",
                language="es",
                query=query,
            )
        )
    return items
