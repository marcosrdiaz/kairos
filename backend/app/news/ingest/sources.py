"""Forma común de una noticia leída de cualquier fuente, y las claves para no duplicarla.

Funciones puras: sin red ni BD.
"""

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_TRACKING = re.compile(r"^(utm_|fbclid$|gclid$|ncid$|guccounter$|soc_|ref$|cmpid$|taid$)")
_SPACES = re.compile(r"\s+")
_NOT_WORD = re.compile(r"[^a-z0-9 ]")


@dataclass(frozen=True)
class RawNews:
    """Una noticia tal como la da la fuente."""

    url: str
    title: str
    summary: str
    published_at: datetime
    source_name: str
    """Medio que la publica (dominio o nombre de la fuente)."""
    provider: str
    """De dónde la hemos leído: `gdelt`, `yahoo_rss` o `fed_rss`."""
    language: str
    """`en` o `es`."""
    query: str
    """Búsqueda o símbolo con el que se encontró."""


TRUSTED_DOMAINS: dict[str, str] = {
    # En español
    "expansion.com": "Expansión",
    "cincodias.elpais.com": "Cinco Días",
    "elpais.com": "El País",
    "eleconomista.es": "elEconomista",
    "elconfidencial.com": "El Confidencial",
    "europapress.es": "Europa Press",
    "abc.es": "ABC",
    "elmundo.es": "El Mundo",
    "lavanguardia.com": "La Vanguardia",
    "rtve.es": "RTVE",
    "efe.com": "EFE",
    "bolsamania.com": "Bolsamanía",
    "es.investing.com": "Investing.com España",
    "elespanol.com": "El Español",
    "invertia.com": "Invertia",
    "vozpopuli.com": "Vozpópuli",
    "libremercado.com": "Libre Mercado",
    "estrategiasdeinversion.com": "Estrategias de Inversión",
    "xataka.com": "Xataka",
    "bloomberglinea.com": "Bloomberg Línea",
    "infobae.com": "Infobae",
    "cnnespanol.cnn.com": "CNN en Español",
    "20minutos.es": "20minutos",
    "larazon.es": "La Razón",
    "elperiodico.com": "El Periódico",
    "eldiario.es": "elDiario.es",
    "bbva.com": "BBVA",
    # En inglés
    "reuters.com": "Reuters",
    "apnews.com": "AP",
    "cnbc.com": "CNBC",
    "bloomberg.com": "Bloomberg",
    "ft.com": "Financial Times",
    "wsj.com": "The Wall Street Journal",
    "marketwatch.com": "MarketWatch",
    "barrons.com": "Barron's",
    "finance.yahoo.com": "Yahoo Finance",
    "investing.com": "Investing.com",
    "theguardian.com": "The Guardian",
    "bbc.com": "BBC",
    "bbc.co.uk": "BBC",
    "nytimes.com": "The New York Times",
    "forbes.com": "Forbes",
    "fortune.com": "Fortune",
    "businessinsider.com": "Business Insider",
    "economist.com": "The Economist",
    # Fuentes oficiales
    "ecb.europa.eu": "Banco Central Europeo",
    "federalreserve.gov": "Reserva Federal",
}
"""Medios cuyas noticias se guardan. El resto de lo que traen los índices se descarta."""


def trusted_source(domain: str) -> str | None:
    """Nombre del medio si es de confianza (también sus subdominios); si no, `None`."""
    domain = domain.lower().removeprefix("www.")
    best: str | None = None
    for trusted in TRUSTED_DOMAINS:
        if (domain == trusted or domain.endswith(f".{trusted}")) and (
            best is None or len(trusted) > len(best)
        ):
            best = trusted
    return TRUSTED_DOMAINS[best] if best else None


def clean_text(text: str) -> str:
    return _SPACES.sub(" ", text).strip()


def normalize_url(url: str) -> str:
    """Sin fragmento, sin parámetros de seguimiento, sin barra final y con el host en minúsculas.
    `http` y `https` cuentan igual."""
    parts = urlsplit(url.strip())
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query) if not _TRACKING.match(k)])
    path = parts.path.rstrip("/") or "/"
    return urlunsplit(("https", parts.netloc.lower().removeprefix("www."), path, query, ""))


def url_key(url: str) -> str:
    return hashlib.sha256(normalize_url(url).encode()).hexdigest()


def title_key(title: str) -> str:
    """Mismo titular en otro medio o con otra puntuación → misma clave."""
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    words = _NOT_WORD.sub(" ", ascii_title.lower()).split()
    return hashlib.sha256(" ".join(words).encode()).hexdigest()


def news_id(url: str) -> str:
    return f"news_{url_key(url)[:12]}"
