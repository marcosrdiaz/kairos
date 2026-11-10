"""RSS de Yahoo Finance (noticias por símbolo) y de la Reserva Federal (política monetaria).

Los dos solo dan las últimas entradas, no histórico: sirven para lo que pasa cada día. Funciones
puras: sin red ni BD. `xml.etree` usa el expat de Python 3.12, que limita la expansión de
entidades.
"""

import html
import re
import xml.etree.ElementTree as ET
from datetime import UTC
from email.utils import parsedate_to_datetime
from urllib.parse import quote

from app.news.ingest.sources import RawNews, clean_text

YAHOO_URL = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbols}&region=US&lang=en-US"
FED_URL = "https://www.federalreserve.gov/feeds/press_monetary.xml"
MAX_SUMMARY = 400
_TAGS = re.compile(r"<[^>]+>")


def yahoo_url(symbols: list[str]) -> str:
    return YAHOO_URL.format(symbols=quote(",".join(symbols), safe=","))


def _summary(raw: str) -> str:
    text = clean_text(_TAGS.sub(" ", html.unescape(raw)))
    return text if len(text) <= MAX_SUMMARY else text[: MAX_SUMMARY - 1].rstrip() + "…"


def parse(xml_text: str, *, provider: str, source_name: str, query: str) -> list[RawNews]:
    """Entradas con enlace, titular y fecha válidos; las demás se ignoran."""
    root = ET.fromstring(xml_text)
    items: list[RawNews] = []
    for item in root.iter("item"):
        link = (item.findtext("link") or "").strip()
        title = clean_text(item.findtext("title") or "")
        raw_date = (item.findtext("pubDate") or "").strip()
        if not link or not title or not raw_date:
            continue
        try:
            published = parsedate_to_datetime(raw_date)
        except (TypeError, ValueError):
            continue
        if published.tzinfo is None:
            continue
        items.append(
            RawNews(
                url=link,
                title=title,
                summary=_summary(item.findtext("description") or ""),
                published_at=published.astimezone(UTC),
                source_name=source_name,
                provider=provider,
                language="en",
                query=query,
            )
        )
    return items


def parse_yahoo(xml_text: str, symbols: list[str]) -> list[RawNews]:
    return parse(
        xml_text, provider="yahoo_rss", source_name="Yahoo Finance", query=",".join(symbols)
    )


def parse_fed(xml_text: str) -> list[RawNews]:
    return parse(
        xml_text, provider="fed_rss", source_name="Reserva Federal", query="press_monetary"
    )
