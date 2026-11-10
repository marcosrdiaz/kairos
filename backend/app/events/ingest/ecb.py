"""Notas de prensa del BCE (RSS oficial) → `EventIn` (T4-05). Funciones puras: sin red ni BD.

Del RSS de `https://www.ecb.europa.eu/rss/press.html` solo cuentan las **decisiones de política
monetaria** (`/press/pr/…/ecb.mp…`): discursos, entrevistas y el resto de notas no mueven los
factores de la cartera. El texto del evento sale de la propia nota (versión en español si existe).

`xml.etree` usa el expat que trae Python 3.12, que ya limita la expansión de entidades.
"""

import hashlib
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser

from app.schemas.events import EventIn, EventType

FEED_URL = "https://www.ecb.europa.eu/rss/press.html"
_POLICY_URL = re.compile(r"/press/pr/date/\d{4}/html/ecb\.mp\d{6}[^/]*\.html$")
_LANG_SUFFIX = re.compile(r"\.[a-z]{2}\.html$")
_SPACES = re.compile(r"[ \t\r\n\f\v]+")  # sin `\xa0`: conserva «2 %» sin partir

FALLBACK_CHAIN = [
    "El Consejo de Gobierno del BCE publica sus decisiones de política monetaria",
    "Los mercados reaccionan a los tipos de interés y al tono del comunicado",
    "Los bonos, el euro y las bolsas recogen la reacción en la sesión de la decisión",
]


@dataclass(frozen=True)
class FeedItem:
    url: str
    title: str
    published: datetime


def normalize_url(url: str) -> str:
    """El RSS del BCE trae `https://www.ecb.europa.eu//press/…` (doble barra)."""
    scheme, sep, rest = url.strip().partition("://")
    return f"{scheme}{sep}{re.sub('/{2,}', '/', rest)}" if sep else url.strip()


def is_policy_decision(url: str) -> bool:
    return _POLICY_URL.search(normalize_url(url)) is not None


def event_id(url: str) -> str:
    """Clave del evento: la URL de la nota sin el idioma, para que la versión en inglés y en
    español de una misma nota sean un solo evento."""
    base = _LANG_SUFFIX.sub("", normalize_url(url))
    return f"bce-{hashlib.sha256(base.encode()).hexdigest()[:12]}"


def language_url(url: str, lang: str) -> str:
    return _LANG_SUFFIX.sub(f".{lang}.html", normalize_url(url))


def parse_feed(xml_text: str) -> list[FeedItem]:
    """Entradas del RSS con enlace y fecha válidos; las demás se ignoran."""
    root = ET.fromstring(xml_text)
    items: list[FeedItem] = []
    for item in root.iter("item"):
        link = (item.findtext("link") or "").strip()
        title = _SPACES.sub(" ", item.findtext("title") or "").strip()
        raw_date = (item.findtext("pubDate") or "").strip()
        if not link or not raw_date:
            continue
        try:
            published = parsedate_to_datetime(raw_date)
        except (TypeError, ValueError):
            continue
        if published.tzinfo is None:
            continue
        items.append(FeedItem(normalize_url(link), title, published.astimezone(UTC)))
    return items


class _ReleaseParser(HTMLParser):
    """Título (`<h1>` dentro de `<main>`) y párrafos del primer `div.section` de la nota."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.paragraphs: list[str] = []
        self._in_main = False
        self._in_h1 = False
        self._section_depth = 0  # profundidad de `div` dentro de la sección; 0 = fuera
        self._section_done = False
        self._paragraph: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = (dict(attrs).get("class") or "").split()
        if tag == "main":
            self._in_main = True
        elif tag == "h1" and self._in_main and not self.title:
            self._in_h1 = True
        elif tag == "div" and self._in_main:
            if self._section_depth:
                self._section_depth += 1
            elif "section" in classes and not self._section_done:
                self._section_depth = 1
        elif tag == "p" and self._section_depth and "ecb-publicationDate" not in classes:
            self._paragraph = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "h1":
            self._in_h1 = False
        elif tag == "p" and self._paragraph is not None:
            text = _SPACES.sub(" ", "".join(self._paragraph)).strip()
            if text:
                self.paragraphs.append(text)
            self._paragraph = None
        elif tag == "div" and self._section_depth:
            self._section_depth -= 1
            if not self._section_depth:
                self._section_done = True

    def handle_data(self, data: str) -> None:
        if self._in_h1:
            self.title += data
        if self._paragraph is not None:
            self._paragraph.append(data)


def parse_release(html_text: str) -> tuple[str, str]:
    """`(título, texto)` de la nota. `ValueError` si no tiene texto."""
    parser = _ReleaseParser()
    parser.feed(html_text)
    parser.close()
    text = "\n\n".join(parser.paragraphs)
    if not text:
        raise ValueError("La nota del BCE no tiene texto")
    return _SPACES.sub(" ", parser.title).strip(), text


def build_event(item: FeedItem, title: str, text: str, url: str) -> EventIn:
    """Evento real sin `observed`: lo mide `events.service.ingest` con los cierres (D-096)."""
    return EventIn(
        id=event_id(item.url),
        type=EventType.CENTRAL_BANK,
        title=f"BCE: {title or item.title}",
        occurred_at=item.published,
        text=text,
        source_urls=[url],
        observed=None,
        fallback_chain=list(FALLBACK_CHAIN),
        illustrative=False,
    )
