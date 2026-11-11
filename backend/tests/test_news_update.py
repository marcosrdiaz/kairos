"""Ingesta periódica de noticias (TB-01): `scripts/news_update.py` y `news.service.refresh`.

Sin red: las fuentes responden con `httpx.MockTransport` y el reloj está fijo.
"""

import importlib.util
import sys
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType
from typing import Any
from urllib.parse import unquote_plus

import httpx
import pytest

from app.core import clock
from app.news import repository, service
from app.news.ingest import runner, topics
from app.news.ingest.runner import SourceSchedule
from app.news.ingest.sources import RawNews

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "news_update.py"
NOW = datetime(2026, 11, 11, 13, 0, tzinfo=UTC)
FIVE = timedelta(minutes=5)

GOOGLE_RSS = """<?xml version="1.0"?><rss><channel>
<item><title>Nvidia presenta resultados - Expansión</title>
<link>https://news.google.com/rss/articles/nvda-11?oc=5</link>
<pubDate>Wed, 11 Nov 2026 12:10:00 GMT</pubDate>
<source url="https://www.expansion.com">Expansión</source></item>
</channel></rss>"""
EMPTY_RSS = '<?xml version="1.0"?><rss><channel></channel></rss>'


@pytest.fixture(scope="module")
def news_update() -> ModuleType:
    spec = importlib.util.spec_from_file_location("news_update", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["news_update"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def _clock() -> None:
    clock.set_now(NOW)


class _Sources:
    """Google Noticias, Yahoo y la Fed falsos: cuentan las peticiones y pueden fallar."""

    def __init__(self, google: str = GOOGLE_RSS, google_status: int = 200) -> None:
        self.google = google
        self.google_status = google_status
        self.urls: list[str] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        self.urls.append(url)
        if "news.google.com" in url:
            return httpx.Response(self.google_status, text=self.google)
        return httpx.Response(200, text=EMPTY_RSS)

    def client(self) -> httpx.Client:
        return httpx.Client(transport=httpx.MockTransport(self.handler))

    def count(self, host: str) -> int:
        return sum(host in url for url in self.urls)


def _schedules() -> dict[str, SourceSchedule]:
    return {
        "google": SourceSchedule(interval=timedelta(minutes=15)),
        "rss": SourceSchedule(interval=FIVE),
    }


def _no_sleep(_: float) -> None:
    return None


# --- Cuándo toca cada fuente (puro) ---


def test_a_new_source_is_due_and_waits_its_interval_after_a_pass() -> None:
    schedule = SourceSchedule(interval=FIVE)
    assert schedule.is_due(NOW)
    schedule.succeeded(NOW)
    assert not schedule.is_due(NOW + FIVE - timedelta(seconds=1))
    assert schedule.is_due(NOW + FIVE)


def test_a_limited_source_waits_twice_as_long_each_time_up_to_one_hour() -> None:
    schedule = SourceSchedule(interval=timedelta(minutes=15))
    waits = []
    when = NOW
    for _ in range(4):
        schedule.limited(when)
        assert schedule.next_at is not None
        waits.append(schedule.next_at - when)
        when = schedule.next_at
    assert waits == [
        timedelta(minutes=30),
        timedelta(hours=1),
        timedelta(hours=1),
        timedelta(hours=1),
    ]
    schedule.succeeded(when)
    assert schedule.next_at == when + timedelta(minutes=15)


# --- Una pasada ---


def test_google_stops_for_the_pass_when_it_limits_us(db: None) -> None:
    sources = _Sources(google="", google_status=429)
    report = runner.run_once(NOW - timedelta(days=1), NOW, http=sources.client(), sleep=_no_sleep)
    assert sources.count("news.google.com") == 1  # no sigue con las otras 16 búsquedas
    assert report.limited == {"google"}
    assert sources.count("finance.yahoo.com") == len(topics.yahoo_symbols())  # el resto sigue


def test_refresh_saves_new_news_and_does_not_repeat_them(db: None) -> None:
    sources = _Sources()
    schedules = _schedules()
    first = service.refresh(schedules, http=sources.client(), sleep=_no_sleep)
    assert first is not None and len(first.created) == 1
    assert sources.count("news.google.com") == len(topics.google_searches())

    clock.set_now(NOW + timedelta(minutes=15))
    again = service.refresh(schedules, http=sources.client(), sleep=_no_sleep)
    assert again is not None and again.created == []
    assert len(repository.list_items()) == 1


def test_refresh_only_reads_the_sources_that_are_due(db: None) -> None:
    sources = _Sources()
    schedules = _schedules()
    service.refresh(schedules, http=sources.client(), sleep=_no_sleep)
    google_before = sources.count("news.google.com")
    rss_before = sources.count("finance.yahoo.com")

    clock.set_now(NOW + FIVE)  # toca el RSS (5 min) y no Google (15 min)
    report = service.refresh(schedules, http=sources.client(), sleep=_no_sleep)
    assert report is not None
    assert sources.count("news.google.com") == google_before
    assert sources.count("finance.yahoo.com") == 2 * rss_before


def test_a_limited_source_backs_off_and_the_rest_keeps_going(db: None) -> None:
    sources = _Sources(google="", google_status=429)
    schedules = _schedules()
    report = service.refresh(schedules, http=sources.client(), sleep=_no_sleep)
    assert report is not None and report.limited == {"google"}
    assert schedules["google"].next_at == NOW + timedelta(minutes=30)
    assert schedules["rss"].next_at == NOW + FIVE


def _latest(published: datetime) -> None:
    raw = RawNews(
        "https://www.expansion.com/x", "Una", "", published, "Expansión", "google_rss", "es", "ITX"
    )
    repository.save_new([raw], NOW)


def _google_window(sources: _Sources) -> str:
    first = next(unquote_plus(u) for u in sources.urls if "news.google.com" in u)
    return first.split("after:")[1].split("&")[0]


@pytest.mark.parametrize(
    ("latest", "after"),
    [
        (None, "2026-11-04 before:2026-11-12"),  # vacía: la última semana
        (NOW - timedelta(hours=1), "2026-11-10 before:2026-11-12"),  # al día: solape de 1 día
        (NOW - timedelta(days=3), "2026-11-08 before:2026-11-12"),  # parada 3 días: desde ahí
        (NOW - timedelta(days=30), "2026-11-04 before:2026-11-12"),  # como mucho 7 días
    ],
)
def test_the_window_starts_at_the_latest_saved_news(
    db: None, latest: datetime | None, after: str
) -> None:
    if latest is not None:
        _latest(latest)
    sources = _Sources(google=EMPTY_RSS)
    service.refresh(_schedules(), http=sources.client(), sleep=_no_sleep)
    assert _google_window(sources) == after


def test_never_two_passes_at_once(db: None) -> None:
    with service.refresh_lock():
        result: list[Any] = []
        worker = threading.Thread(
            target=lambda: result.append(
                service.refresh(_schedules(), http=_Sources().client(), sleep=_no_sleep)
            )
        )
        worker.start()
        worker.join()
    assert result == [None]


# --- El script ---


class _Calls:
    def __init__(self, created: list[str], classified: int) -> None:
        self.created = created
        self.classified = classified
        self.checked: list[tuple[str, bool]] = []
        self.refreshed = 0

    def refresh(self, schedules: dict[str, SourceSchedule]) -> runner.NewsIngestReport:
        self.refreshed += 1
        return runner.NewsIngestReport(created=list(self.created), read=len(self.created))

    def classify(self) -> int:
        return self.classified

    def check_news(self, portfolio_id: str, *, force: bool = False) -> int:
        self.checked.append((portfolio_id, force))
        return 0


def _wire(monkeypatch: pytest.MonkeyPatch, calls: _Calls) -> None:
    from app.alerts import service as alerts_service
    from app.portfolio import service as portfolio_service

    monkeypatch.setattr(service, "refresh", calls.refresh)
    monkeypatch.setattr(service, "classify_pending", calls.classify)
    monkeypatch.setattr(alerts_service, "check_news", calls.check_news)
    monkeypatch.setattr(portfolio_service, "list_portfolio_ids", lambda: ["laura", "javier"])


def test_demo_mode_does_not_poll(news_update: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _Calls(["n1"], 1)
    _wire(monkeypatch, calls)
    monkeypatch.setenv("DEMO_MODE", "true")
    from app.config import get_settings

    get_settings.cache_clear()
    try:
        assert news_update.main(["--once"]) == 0
    finally:
        get_settings.cache_clear()
    assert calls.refreshed == 0


def test_a_pass_classifies_and_logs_one_line(
    news_update: ModuleType, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    calls = _Calls(["n1", "n2"], 2)
    _wire(monkeypatch, calls)
    caplog.set_level("INFO", logger="news_update")
    result = news_update.poll_once(_schedules())
    assert result.classified == 2
    lines = [r.getMessage() for r in caplog.records if r.name == "news_update"]
    assert len(lines) == 1
    assert "2 nuevas" in lines[0] and "2 clasificadas" in lines[0]


def test_a_pass_while_another_runs_is_skipped(
    news_update: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _Calls([], 0)
    _wire(monkeypatch, calls)
    monkeypatch.setattr(service, "refresh", lambda schedules: None)
    result = news_update.poll_once(_schedules())
    assert result.skipped and calls.checked == []


def test_an_unexpected_error_does_not_stop_the_loop(
    news_update: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(schedules: dict[str, SourceSchedule]) -> None:
        raise RuntimeError("BD caída")

    monkeypatch.setattr(service, "refresh", boom)
    assert news_update.safe_poll(_schedules()) is None
