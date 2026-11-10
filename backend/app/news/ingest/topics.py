"""Qué se busca: las empresas del catálogo y las grandes de dentro de los fondos, y los temas
generales que mueven los cinco factores (bancos centrales, petróleo, divisas, política comercial
y bolsa).

`key` de cada empresa = `constituent_key` de las composiciones y `ticker` del catálogo: es la
clave con la que el motor de impacto encuentra la exposición, directa o dentro de un fondo.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Company:
    key: str
    name: str
    search: str
    """Búsqueda (vale para Google Noticias y para GDELT)."""
    yahoo: str | None
    """Símbolo en Yahoo Finance para su RSS; `None` si no está en el catálogo."""
    asset_id: str | None = None
    """ISIN en el catálogo (con precios para medir su movimiento); `None` si no está."""


@dataclass(frozen=True)
class Topic:
    key: str
    search_en: str
    search_es: str


COMPANIES: tuple[Company, ...] = (
    Company("AAPL", "Apple", "Apple", "AAPL", "US0378331005"),
    Company("NVDA", "NVIDIA", "Nvidia", "NVDA", "US67066G1040"),
    Company("MSFT", "Microsoft", "Microsoft", "MSFT", "US5949181045"),
    Company("AMZN", "Amazon", "Amazon", "AMZN", "US0231351067"),
    Company("GOOGL", "Alphabet", "(Alphabet OR Google)", "GOOGL", "US02079K3059"),
    Company("META", "Meta Platforms", '("Meta Platforms" OR Zuckerberg)', "META", "US30303M1027"),
    Company("TSLA", "Tesla", "Tesla", "TSLA", "US88160R1014"),
    Company("ASML", "ASML", "ASML", "ASML.AS", "NL0010273215"),
    Company("ITX", "Inditex", "Inditex", "ITX.MC", "ES0148396007"),
    Company("IBE", "Iberdrola", "Iberdrola", "IBE.MC", "ES0144580Y14"),
    Company("AVGO", "Broadcom", "Broadcom", None),
)

TOPICS: tuple[Topic, ...] = (
    Topic("ecb", '"European Central Bank"', "(BCE OR Lagarde) tipos"),
    Topic("fed", '"Federal Reserve"', '("Reserva Federal" OR Powell)'),
    Topic("oil", '(OPEC OR "oil prices")', "(OPEP OR petróleo OR Brent)"),
    Topic("fx", '"euro dollar"', '("euro dólar" OR "tipo de cambio" euro)'),
    Topic("trade", '(tariffs OR "trade war")', "aranceles"),
    Topic("markets", '("stock market" OR "Wall Street")', '("Wall Street" OR "Ibex 35")'),
)


def yahoo_symbols() -> list[str]:
    return [c.yahoo for c in COMPANIES if c.yahoo]


def google_searches() -> list[tuple[str, str]]:
    """`(clave, búsqueda)` de cada consulta a Google Noticias (edición España)."""
    return [(c.key, c.search) for c in COMPANIES] + [(t.key, t.search_es) for t in TOPICS]


def gdelt_searches() -> list[tuple[str, str, str]]:
    """`(clave, búsqueda, idioma)` de cada consulta a GDELT."""
    out = [(c.key, c.search, "en") for c in COMPANIES]
    for topic in TOPICS:
        out += [(topic.key, topic.search_en, "en"), (topic.key, topic.search_es, "es")]
    return out
