"""`prices`: `latest`, `history` y `fx_rate` con el proveedor falso y el CSV offline (T1-02)."""

from collections.abc import Iterator
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from app.core import clock
from app.core.errors import AppError, ErrorCode
from app.prices import service
from app.prices.provider import OfflineCsvProvider, PricePoint
from app.schemas.common import PriceKind, SourceKind
from tests.fakes.price_provider import FakePriceProvider, use_price_provider

IWDA = "IE00B4L5Y983"  # ETF en EUR, intradía
VANGUARD = "IE00B03HD191"  # fondo en EUR, VL diario
APPLE = "US0378331005"  # acción en USD
DEPOSIT = "DEP-12M"  # fixed:1
PENSION = "PP-MIXTO"  # fixed:10

NOW = datetime(2026, 11, 8, 18, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _fake() -> Iterator[FakePriceProvider]:
    clock.set_now(NOW)
    provider = FakePriceProvider(
        closes={
            IWDA: {"2026-11-05": "95.10", "2026-11-06": "95.42", "2026-11-09": "99.00"},
            VANGUARD: {"2026-11-04": "48.00", "2026-11-06": "48.20"},
            APPLE: {"2026-11-06": "228.10"},
        },
        fx={"EURUSD": {"2026-11-05": "1.1500", "2026-11-06": "1.1600"}},
    )
    with use_price_provider(provider):
        yield provider


# --- latest ---


def test_latest_is_last_close_not_after_clock() -> None:
    out = service.latest(IWDA)
    assert out.asset_id == IWDA
    assert out.price == Decimal("95.42")
    assert out.currency == "EUR"
    assert out.price_kind is PriceKind.INTRADAY
    assert out.price_at == datetime(2026, 11, 6, tzinfo=UTC)


def test_latest_follows_demo_clock() -> None:
    clock.set_now(datetime(2026, 11, 5, 12, 0, tzinfo=UTC))
    assert service.latest(IWDA).price == Decimal("95.10")


def test_latest_fund_is_nav_with_source() -> None:
    out = service.latest(VANGUARD)
    assert out.price_kind is PriceKind.NAV_DAILY
    assert out.source.kind is SourceKind.PRICE
    assert out.source.ref == VANGUARD
    assert out.source.as_of == out.price_at
    assert "Vanguard Global Stock Index" in out.source.label


def test_latest_keeps_asset_currency() -> None:
    out = service.latest(APPLE)
    assert out.currency == "USD"
    assert out.price == Decimal("228.10")


@pytest.mark.parametrize(("asset_id", "value"), [(DEPOSIT, "1"), (PENSION, "10")])
def test_latest_fixed_price_is_constant_at_today(asset_id: str, value: str) -> None:
    out = service.latest(asset_id)
    assert out.price == Decimal(value)
    assert out.price_at == datetime(2026, 11, 8, tzinfo=UTC)


def test_latest_unknown_asset_is_not_found() -> None:
    with pytest.raises(AppError) as exc:
        service.latest("XX0000000000")
    assert exc.value.code is ErrorCode.NOT_FOUND


def test_latest_without_data_is_price_unavailable() -> None:
    with pytest.raises(AppError) as exc:
        service.latest("IE00B5BMR087")  # en el catálogo, sin precios en el proveedor
    assert exc.value.code is ErrorCode.PRICE_UNAVAILABLE
    assert exc.value.details["asset_id"] == "IE00B5BMR087"


def test_latest_before_first_close_is_price_unavailable() -> None:
    clock.set_now(datetime(2026, 1, 1, tzinfo=UTC))
    with pytest.raises(AppError) as exc:
        service.latest(IWDA)
    assert exc.value.code is ErrorCode.PRICE_UNAVAILABLE


# --- history ---


def test_history_is_inclusive_and_ordered() -> None:
    out = service.history(IWDA, date(2026, 11, 5), date(2026, 11, 9))
    assert [p.price for p in out] == [Decimal("95.10"), Decimal("95.42"), Decimal("99.00")]
    assert [p.price_at.day for p in out] == [5, 6, 9]


def test_history_fixed_price_has_one_point_per_day() -> None:
    out = service.history(DEPOSIT, date(2026, 11, 1), date(2026, 11, 3))
    assert [p.price for p in out] == [Decimal("1")] * 3


def test_history_empty_range() -> None:
    assert service.history(IWDA, date(2026, 11, 7), date(2026, 11, 8)) == []


# --- fx_rate ---


def test_fx_direct_pair() -> None:
    assert service.fx_rate("EURUSD") == Decimal("1.1600")


def test_fx_inverse_pair() -> None:
    rate = service.fx_rate("USDEUR")
    assert rate == (Decimal(1) / Decimal("1.1600")).quantize(Decimal("0.00000001"))


def test_fx_same_currency_is_one() -> None:
    assert service.fx_rate("EUREUR") == Decimal(1)


def test_fx_at_past_instant() -> None:
    assert service.fx_rate("EURUSD", datetime(2026, 11, 5, 20, 0, tzinfo=UTC)) == Decimal("1.15")


def test_fx_quote_carries_source() -> None:
    quote = service.fx_quote("USDEUR")
    assert quote.pair == "USDEUR"
    assert quote.at == datetime(2026, 11, 6, tzinfo=UTC)
    assert quote.source.kind is SourceKind.FX
    assert quote.source.ref == "EURUSD"


@pytest.mark.parametrize("pair", ["EURGBP", "eurusd", "EUR"])
def test_fx_unknown_or_bad_pair(pair: str) -> None:
    with pytest.raises(AppError) as exc:
        service.fx_rate(pair)
    assert exc.value.code in {ErrorCode.PRICE_UNAVAILABLE, ErrorCode.VALIDATION_ERROR}


# --- Proveedor offline (CSV) ---


def test_offline_csv_provider_reads_closes_and_fx(tmp_path: Path) -> None:
    """Formato de T1-09: `data/prices` (`date,close,adj_close`) y `data/factors` (`date,value`)."""
    (tmp_path / f"{IWDA}.csv").write_text(
        "date,close,adj_close\n2026-11-06,95.42,95.42\n2026-11-05,95.10,94.00\n\n",
        encoding="utf-8",
    )
    (tmp_path / "EURUSD.csv").write_text("date,value\n2026-11-06,1.16\n", encoding="utf-8")
    provider = OfflineCsvProvider(prices_dir=tmp_path, factors_dir=tmp_path)
    assert provider.closes(IWDA) == [
        PricePoint(date(2026, 11, 5), Decimal("95.10")),
        PricePoint(date(2026, 11, 6), Decimal("95.42")),
    ]
    assert provider.fx_closes("EURUSD") == [PricePoint(date(2026, 11, 6), Decimal("1.16"))]


def test_offline_csv_provider_missing_file_is_empty(tmp_path: Path) -> None:
    provider = OfflineCsvProvider(prices_dir=tmp_path, factors_dir=tmp_path)
    assert provider.closes(IWDA) == []
    assert provider.fx_closes("EURUSD") == []


def test_offline_csv_provider_rejects_bad_rows(tmp_path: Path) -> None:
    (tmp_path / f"{IWDA}.csv").write_text("date,close\n2026-11-06,abc\n", encoding="utf-8")
    with pytest.raises(ValueError, match=IWDA):
        OfflineCsvProvider(prices_dir=tmp_path).closes(IWDA)


def test_default_provider_is_offline() -> None:
    service.set_provider(None)
    assert isinstance(service.get_provider(), OfflineCsvProvider)


def test_repo_data_values_seed_assets() -> None:
    """Con los CSV reales de T1-09, los activos del seed tienen precio y el USD, tipo de cambio."""
    service.set_provider(None)
    for asset_id in (IWDA, VANGUARD, APPLE, DEPOSIT, PENSION, "IE0007472115"):
        assert service.latest(asset_id).price > 0
    assert Decimal("0.5") < service.fx_rate("USDEUR") < Decimal("1.5")
