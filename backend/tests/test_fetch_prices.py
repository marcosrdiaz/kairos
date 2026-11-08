"""`scripts/fetch_prices.py`: sesión que recoge el evento, variaciones y `observed` reproducible."""

import importlib.util
import json
import sys
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "fetch_prices.py"


@pytest.fixture(scope="module")
def fetch() -> ModuleType:
    spec = importlib.util.spec_from_file_location("fetch_prices", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_reaction_date_same_day_before_us_close(fetch: ModuleType) -> None:
    assert fetch.reaction_date(datetime(2025, 6, 5, 12, 15, tzinfo=UTC)) == date(2025, 6, 5)


def test_reaction_date_next_day_after_us_close(fetch: ModuleType) -> None:
    assert fetch.reaction_date(datetime(2025, 2, 26, 21, 20, tzinfo=UTC)) == date(2025, 2, 27)


def test_series_change_relative(fetch: ModuleType) -> None:
    series = [(date(2025, 2, 26), Decimal("100")), (date(2025, 2, 27), Decimal("91.5"))]
    assert fetch.series_change(series, date(2025, 2, 27)) == Decimal("-0.08500")


def test_series_change_absolute_for_rates(fetch: ModuleType) -> None:
    series = [(date(2025, 6, 4), Decimal("0.0262")), (date(2025, 6, 5), Decimal("0.0252"))]
    assert fetch.series_change(series, date(2025, 6, 5), absolute=True) == Decimal("-0.00100")


def test_series_change_uses_first_session_from_day(fetch: ModuleType) -> None:
    series = [(date(2025, 6, 13), Decimal("100")), (date(2025, 6, 16), Decimal("110"))]
    assert fetch.series_change(series, date(2025, 6, 14)) == Decimal("0.10000")


def test_series_change_needs_previous_session(fetch: ModuleType) -> None:
    with pytest.raises(ValueError):
        fetch.series_change([(date(2025, 6, 5), Decimal("1"))], date(2025, 6, 5))


def _yahoo(timestamps: list[int], closes: list[float | None]) -> dict[str, Any]:
    quote = {"close": closes}
    indicators = {"quote": [quote], "adjclose": [{"adjclose": closes}]}
    return {"chart": {"result": [{"timestamp": timestamps, "indicators": indicators}]}}


def test_parse_yahoo_drops_gaps_weekends_and_open_session(fetch: ModuleType) -> None:
    timestamps = [
        1749130200,  # jueves 2025-06-05, apertura en Nueva York
        1749216600,  # viernes 2025-06-06, sin cierre
        1749389400,  # domingo 2025-06-08
        1749475800,  # lunes 2025-06-09, hoy
    ]
    rows = fetch.parse_yahoo(_yahoo(timestamps, [1.5, None, 3.0, 4.0]), 4, date(2025, 6, 9))
    assert rows == [("2025-06-05", "1.5000", "1.5000")]


def test_bar_date_with_midnight_new_york_in_summer(fetch: ModuleType) -> None:
    assert fetch._bar_date(1749787200) == date(2025, 6, 13)  # 2025-06-13 04:00 UTC


def test_parse_ecb_rates_converts_percent_to_fraction(fetch: ModuleType) -> None:
    text = "TIME_PERIOD,OBS_VALUE\n2025-06-05,2.6470041589\n2025-06-06,\n"
    assert fetch.parse_ecb_rates(text, date(2025, 6, 9)) == [("2025-06-05", "0.026470041589")]


@pytest.mark.parametrize(
    "path", sorted(Path(SCRIPT.parents[1], "data/events/replay").glob("*.json"))
)
def test_committed_observed_matches_csv(fetch: ModuleType, path: Path) -> None:
    event = json.loads(path.read_text(encoding="utf-8"))
    assert event["observed"] == fetch.compute_observed(event)
