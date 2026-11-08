from datetime import UTC, datetime, timedelta, timezone

import pytest

from app.config import get_settings
from app.core import clock


def test_now_is_utc_aware() -> None:
    value = clock.now()
    assert value.tzinfo is not None
    assert value.utcoffset() == timedelta(0)


def test_demo_clock_env_fixes_now(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_CLOCK", "2026-11-08T18:00:00Z")
    get_settings.cache_clear()
    assert clock.now() == datetime(2026, 11, 8, 18, 0, tzinfo=UTC)


def test_set_now_overrides_and_converts_to_utc() -> None:
    madrid = timezone(timedelta(hours=1))
    clock.set_now(datetime(2026, 11, 8, 19, 0, tzinfo=madrid))
    assert clock.now() == datetime(2026, 11, 8, 18, 0, tzinfo=UTC)
    assert clock.now().tzinfo == UTC


def test_set_now_none_returns_to_real_clock_even_with_demo_clock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DEMO_CLOCK", "2020-01-01T00:00:00Z")
    get_settings.cache_clear()
    clock.set_now(None)
    assert clock.now().year >= 2026


def test_set_now_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError):
        clock.set_now(datetime(2026, 11, 8, 18, 0))  # noqa: DTZ001


def test_demo_clock_without_timezone_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_CLOCK", "2026-11-08T18:00:00")
    get_settings.cache_clear()
    with pytest.raises(ValueError):
        clock.now()
