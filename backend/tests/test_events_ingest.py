"""Ingesta de noticias del BCE (T4-05). Fuentes leídas de texto, sin red (`httpx.MockTransport`)."""

from datetime import UTC, datetime

import httpx
import pytest

from app.core import clock
from app.events import repository
from app.events import service as events_service
from app.events.ingest import ecb, runner
from app.schemas.events import EventIn, EventType, ReplayOut

_BASE = "https://www.ecb.europa.eu/press/pr/date/2026/html"
_MP = f"{_BASE}/ecb.mp261029~9a493adf17"
_FEED = """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0"><channel><title>ECB</title>
<item><title> Philip R. Lane: The science of communication</title>
<link>https://www.ecb.europa.eu//press/key/date/2026/html/ecb.sp261110_1~9725b7aa07.en.html</link>
<pubDate>Tue, 10 Nov 2026 17:45:00 +0100</pubDate></item>
<item><title> ECB publishes consolidated banking data</title>
<link>https://www.ecb.europa.eu//press/pr/date/2026/html/ecb.pr261106~356f2fc73a.en.html</link>
<pubDate>Fri, 06 Nov 2026 10:00:00 +0100</pubDate></item>
<item><title> Monetary policy decisions</title>
<link>https://www.ecb.europa.eu//press/pr/date/2026/html/ecb.mp261029~9a493adf17.en.html</link>
<pubDate>Thu, 29 Oct 2026 14:15:00 +0100</pubDate></item>
<item><title> Monetary policy decisions</title>
<link>https://www.ecb.europa.eu//press/pr/date/2026/html/ecb.mp260716~0123456789.en.html</link>
<pubDate>Thu, 16 Jul 2026 14:15:00 +0200</pubDate></item>
<item><title>Sin fecha</title><link>https://www.ecb.europa.eu/x.html</link></item>
</channel></rss>"""
_RELEASE_ES = """<html><head><title>Decisiones de política monetaria</title></head><body>
<header><h1 class="ecb0 title-stick">Search Results</h1></header>
<main ><div class="title"><h1>Decisiones de política monetaria</h1></div>
<div class="section"><p class="ecb-publicationDate">29 de octubre de 2026</p>
<p>El Consejo de Gobierno ha decidido hoy mantener sin variación los tres tipos de interés
oficiales del BCE.</p><div class="inner"><p>Objetivo del 2&nbsp;% a medio plazo.</p></div>
<p>   </p></div>
<div class="section"><p>Contacto con los medios</p></div></main></body></html>"""
_NOW = datetime(2026, 11, 10, 18, 0, tzinfo=UTC)


def _transport(pages: dict[str, str], calls: list[str] | None = None) -> httpx.Client:
    def handle(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if calls is not None:
            calls.append(url)
        if url in pages:
            return httpx.Response(200, text=pages[url])
        return httpx.Response(404, text="no")

    return httpx.Client(transport=httpx.MockTransport(handle))


def _sources() -> dict[str, str]:
    return {ecb.FEED_URL: _FEED, f"{_MP}.es.html": _RELEASE_ES}


@pytest.fixture
def production(monkeypatch: pytest.MonkeyPatch, db: None) -> None:
    from app.config import get_settings

    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "yahoo")
    get_settings.cache_clear()
    clock.set_now(_NOW)


class _Recorder:
    def __init__(self) -> None:
        self.events: list[EventIn] = []

    def __call__(self, event: EventIn, companies: dict[str, str] | None) -> ReplayOut | None:
        self.events.append(event)
        return None


# --- Funciones puras ---


def test_feed_keeps_items_with_link_and_date_and_fixes_the_double_slash() -> None:
    items = ecb.parse_feed(_FEED)
    assert len(items) == 4
    assert items[2].url == f"{_MP}.en.html"
    assert items[2].published == datetime(2026, 10, 29, 13, 15, tzinfo=UTC)


def test_only_monetary_policy_decisions_count() -> None:
    flags = [ecb.is_policy_decision(item.url) for item in ecb.parse_feed(_FEED)]
    assert flags == [False, False, True, True]


def test_event_id_is_the_url_without_language() -> None:
    assert ecb.event_id(f"{_MP}.en.html") == ecb.event_id(f"{_MP}.es.html")
    assert ecb.event_id(f"{_MP}.en.html") != ecb.event_id(
        f"{_BASE}/ecb.mp260716~0123456789.en.html"
    )
    assert ecb.event_id(f"{_MP}.en.html").startswith("bce-")


def test_release_text_is_the_first_section_without_the_date() -> None:
    title, text = ecb.parse_release(_RELEASE_ES)
    assert title == "Decisiones de política monetaria"
    assert text.startswith("El Consejo de Gobierno ha decidido hoy")
    assert "Objetivo del 2\xa0% a medio plazo." in text
    assert "29 de octubre" not in text
    assert "Contacto" not in text


def test_release_without_text_is_an_error() -> None:
    with pytest.raises(ValueError):
        ecb.parse_release("<html><main><div class='section'></div></main></html>")


def test_built_event_is_real_and_unmeasured() -> None:
    item = ecb.parse_feed(_FEED)[2]
    event = ecb.build_event(item, "Decisiones de política monetaria", "Texto", f"{_MP}.es.html")
    assert event.type is EventType.CENTRAL_BANK
    assert event.observed is None
    assert event.illustrative is False
    assert event.source_urls == [f"{_MP}.es.html"]
    assert event.occurred_at == item.published
    assert not any(char.isdigit() for step in event.fallback_chain for char in step)


# --- Pasada de la ingesta ---


def test_demo_mode_does_nothing(db: None) -> None:
    calls: list[str] = []
    recorder = _Recorder()
    report = runner.run_once(_transport(_sources(), calls), recorder)
    assert calls == [] and recorder.events == [] and report.created == []


def test_creates_one_event_per_recent_policy_decision(production: None) -> None:
    recorder = _Recorder()
    report = runner.run_once(_transport(_sources()), recorder)
    assert [event.id for event in recorder.events] == [ecb.event_id(f"{_MP}.en.html")]
    assert report.created == [recorder.events[0].id] and report.failed == {}
    event = recorder.events[0]
    assert event.title == "BCE: Decisiones de política monetaria"
    assert event.source_urls == [f"{_MP}.es.html"]


def test_falls_back_to_english_if_there_is_no_translation(production: None) -> None:
    pages = {ecb.FEED_URL: _FEED, f"{_MP}.en.html": _RELEASE_ES}
    recorder = _Recorder()
    runner.run_once(_transport(pages), recorder)
    assert recorder.events[0].source_urls == [f"{_MP}.en.html"]


def test_feed_failure_is_reported_and_does_not_raise(production: None) -> None:
    report = runner.run_once(_transport({}), _Recorder())
    assert list(report.failed) == [ecb.FEED_URL]


def test_release_failure_is_reported_and_others_continue(production: None) -> None:
    report = runner.run_once(_transport({ecb.FEED_URL: _FEED}), _Recorder())
    assert report.created == [] and list(report.failed) == [f"{_MP}.en.html"]


def test_new_note_is_saved_pending_and_not_duplicated(production: None) -> None:
    """Con el `ingest` real: el día de la nota aún no ha cerrado, así que queda pendiente con su
    análisis (D-096); la segunda pasada no la vuelve a dar de alta."""
    clock.set_now(datetime(2026, 10, 29, 18, 0, tzinfo=UTC))
    first = runner.run_once(_transport(_sources()))
    event_id = ecb.event_id(f"{_MP}.en.html")
    assert first.created == [event_id] and first.failed == {}
    assert events_service.list_pending() == [event_id]
    saved = repository.get_payload(event_id)
    assert saved is not None and saved.text.startswith("El Consejo de Gobierno")

    second = runner.run_once(_transport(_sources()))
    assert second.created == [] and second.skipped == [event_id]
    assert events_service.list_pending() == [event_id]
