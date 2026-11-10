"""Ingesta de noticias (T4-28): parsers, claves sin duplicados, una pasada y la base exportada.

Sin red: las respuestas de las fuentes son cadenas y `httpx.MockTransport`.
"""

from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from app.core import clock
from app.news import repository, service
from app.news.ingest import gdelt, google, rss, runner, topics
from app.news.ingest.sources import RawNews, normalize_url, title_key, trusted_source

NOV_1 = datetime(2026, 11, 1, tzinfo=UTC)
NOV_10 = datetime(2026, 11, 10, 23, 59, tzinfo=UTC)

GOOGLE_RSS = """<?xml version="1.0"?><rss><channel>
<item><title>Nvidia investiga a su consejero delegado - El Mundo</title>
<link>https://news.google.com/rss/articles/abc?oc=5</link>
<pubDate>Mon, 09 Nov 2026 10:10:07 GMT</pubDate>
<source url="https://www.elmundo.es">El Mundo</source></item>
<item><title>Un blog cualquiera sobre Nvidia - Blog</title>
<link>https://news.google.com/rss/articles/def</link>
<pubDate>Mon, 09 Nov 2026 11:00:00 GMT</pubDate>
<source url="https://blog.example.com">Blog</source></item>
<item><title>Sin fecha - Expansión</title><link>https://news.google.com/x</link>
<source url="https://www.expansion.com">Expansión</source></item>
</channel></rss>"""

YAHOO_RSS = """<?xml version="1.0"?><rss><channel>
<item><title>Iberdrola signs deal</title><link>https://finance.yahoo.com/news/ibe-1.html</link>
<description>&lt;p&gt;Iberdrola &amp;amp; BYD agree.&lt;/p&gt;</description>
<pubDate>Tue, 03 Nov 2026 13:37:23 +0000</pubDate></item>
</channel></rss>"""

GDELT_JSON = """{"articles": [
 {"url": "https://www.reuters.com/a", "title": "ECB holds rates", "seendate": "20261105T130000Z",
  "domain": "reuters.com", "language": "English"},
 {"url": "https://spam.example/b", "title": "ECB", "seendate": "20261105T130000Z",
  "domain": "spam.example", "language": "English"}
]}"""


def _raw(url: str, title: str, when: datetime = NOV_1) -> RawNews:
    return RawNews(url, title, "", when, "Reuters", "gdelt", "en", "NVDA")


# --- Funciones puras ---


def test_google_keeps_trusted_media_and_strips_the_source_from_the_title() -> None:
    items = google.parse(GOOGLE_RSS, "NVDA")
    assert [i.title for i in items] == ["Nvidia investiga a su consejero delegado"]
    assert items[0].source_name == "El Mundo"
    assert items[0].published_at == datetime(2026, 11, 9, 10, 10, 7, tzinfo=UTC)
    assert items[0].provider == "google_rss" and items[0].query == "NVDA"


def test_google_search_url_has_the_date_range() -> None:
    url = google.search_url("Nvidia", NOV_1.date(), NOV_10.date())
    assert "after%3A2026-11-01" in url and "before%3A2026-11-11" in url and "hl=es" in url


def test_yahoo_rss_summary_is_plain_text() -> None:
    [item] = rss.parse_yahoo(YAHOO_RSS, ["IBE.MC"])
    assert item.summary == "Iberdrola & BYD agree."
    assert item.source_name == "Yahoo Finance" and item.query == "IBE.MC"


def test_gdelt_keeps_trusted_media_and_flags_rate_limits() -> None:
    [item] = gdelt.parse(GDELT_JSON, "ecb")
    assert item.source_name == "Reuters" and item.language == "en"
    with pytest.raises(ValueError, match="no ha devuelto JSON"):
        gdelt.parse("Please limit requests to one every 5 seconds", "ecb")


def test_keys_ignore_tracking_and_punctuation() -> None:
    assert normalize_url("http://www.Reuters.com/a/?utm_source=x&id=1#top") == (
        "https://reuters.com/a?id=1"
    )
    assert title_key("¡Nvidia cae!") == title_key("nvidia  cae")
    assert trusted_source("cincodias.elpais.com") == "Cinco Días"
    assert trusted_source("www.elpais.com") == "El País"
    assert trusted_source("elpais.com.fake.net") is None


def test_every_company_has_a_search() -> None:
    keys = {key for key, _ in topics.google_searches()}
    assert {"NVDA", "ITX", "IBE", "ecb", "oil"} <= keys


# --- BD ---


def test_save_new_skips_same_url_and_same_title(db: None) -> None:
    first = repository.save_new([_raw("https://reuters.com/a", "Nvidia cae")], NOV_1)
    again = repository.save_new(
        [
            _raw("https://www.reuters.com/a/?utm_source=x", "Otro titular"),
            _raw("https://cnbc.com/b", "NVIDIA cae"),
            _raw("https://cnbc.com/c", "Nvidia cae", datetime(2026, 11, 9, tzinfo=UTC)),
        ],
        NOV_1,
    )
    assert len(first) == 1
    assert len(again) == 1  # solo el mismo titular días después cuenta como noticia nueva


def test_run_once_reads_sources_and_survives_failures(db: None) -> None:
    clock.set_now(datetime(2026, 11, 10, 22, 0, tzinfo=UTC))

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "news.google.com" in url:
            if "Iberdrola" in url:
                return httpx.Response(500)
            return httpx.Response(200, text=GOOGLE_RSS)
        if "yahoo" in url:
            return httpx.Response(200, text=YAHOO_RSS)
        return httpx.Response(200, text="<rss><channel></channel></rss>")

    http = httpx.Client(transport=httpx.MockTransport(handler))
    report = runner.run_once(NOV_1, NOV_10, http=http, sleep=lambda _: None)
    assert "google:IBE" in report.failed
    assert len(report.created) == 2  # El Mundo (una vez) y Yahoo (una vez)
    again = runner.run_once(NOV_1, NOV_10, http=http, sleep=lambda _: None)
    assert again.created == []


def test_old_periods_do_not_read_the_rss(db: None) -> None:
    clock.set_now(datetime(2026, 11, 30, tzinfo=UTC))
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, text="<rss><channel></channel></rss>")

    http = httpx.Client(transport=httpx.MockTransport(handler))
    runner.run_once(NOV_1, NOV_10, http=http, sleep=lambda _: None)
    assert seen and not any("yahoo" in url or "federalreserve" in url for url in seen)


def test_snapshot_round_trip_keeps_the_classification(db: None, tmp_path: Path) -> None:
    [item_id] = repository.save_new([_raw("https://reuters.com/a", "Nvidia cae")], NOV_1)
    repository.save_classification(item_id, {"category": "company"}, "v1", NOV_1)
    path = tmp_path / "news" / "2026-11.jsonl"
    assert service.export_snapshot(path) == 1
    repository.delete_all()
    assert service.load_snapshot(path.parent) == 1
    row = repository.get_item(item_id)
    assert row is not None and row.classification == {"category": "company"}
    assert service.load_snapshot(path.parent) == 0
