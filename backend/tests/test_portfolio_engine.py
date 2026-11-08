"""Casos límite del motor de valoración (`portfolio/engine.py`, funciones puras)."""

from datetime import UTC, datetime
from decimal import Decimal

from app.portfolio.engine import AssetIn, LotIn, QuoteIn, value_portfolio
from app.schemas.common import AssetClass, AssetType, PriceKind

T0 = datetime(2024, 1, 1, tzinfo=UTC)
T1 = datetime(2025, 1, 1, tzinfo=UTC)
NOW = datetime(2026, 11, 6, tzinfo=UTC)
ETF = AssetIn("A", "A", "AAA", "Activo A", AssetType.ETF, AssetClass.EQUITY, False)
BOND = AssetIn("B", "B", None, "Fondo B", AssetType.FUND, AssetClass.FIXED_INCOME, True)


def _quote(price: str, week: str | None = None, fx: str = "1") -> QuoteIn:
    return QuoteIn(
        price=Decimal(price),
        currency="EUR",
        price_at=NOW,
        price_kind=PriceKind.INTRADAY,
        fx_rate=Decimal(fx),
        week_ago_unit_eur=Decimal(week) if week is not None else None,
    )


def test_empty_portfolio_is_zero() -> None:
    out = value_portfolio([], {}, {})
    assert out.total_eur == 0
    assert out.change_week_eur == 0
    assert out.change_week_pct == 0
    assert out.positions == []
    assert out.allocation.equity == 0


def test_lots_of_same_asset_are_aggregated_with_weighted_cost() -> None:
    lots = [
        LotIn("A", T1, Decimal("1"), Decimal("30")),
        LotIn("A", T0, Decimal("3"), Decimal("10")),
    ]
    out = value_portfolio(lots, {"A": ETF}, {"A": _quote("20")})
    [pos] = out.positions
    assert pos.units == Decimal("4")
    assert pos.avg_cost_eur == Decimal("15.00")  # (30 + 30) / 4
    assert pos.value_eur == Decimal("80.00")
    assert pos.unrealized_pnl_eur == Decimal("20.00")
    assert pos.first_acquired_at == T0
    assert pos.weight == Decimal("1.0000")


def test_exhausted_lots_are_ignored() -> None:
    lots = [LotIn("A", T0, Decimal("0"), Decimal("10")), LotIn("B", T0, Decimal("2"), Decimal("5"))]
    out = value_portfolio(lots, {"A": ETF, "B": BOND}, {"B": _quote("6")})
    assert [p.asset_id for p in out.positions] == ["B"]
    assert out.allocation.fixed_income == Decimal("1.0000")


def test_value_uses_fx_and_rounds_half_even() -> None:
    lots = [LotIn("A", T0, Decimal("1"), Decimal("1"))]
    out = value_portfolio(lots, {"A": ETF}, {"A": _quote("10.005", fx="1")})
    assert out.total_eur == Decimal("10.00")  # 10,005 → 10,00 (al par)
    out = value_portfolio(lots, {"A": ETF}, {"A": _quote("100", fx="0.86206897")})
    assert out.total_eur == Decimal("86.21")


def test_week_change_skips_assets_without_history() -> None:
    lots = [
        LotIn("A", T0, Decimal("10"), Decimal("1")),
        LotIn("B", T0, Decimal("10"), Decimal("1")),
    ]
    quotes = {"A": _quote("11", week="10"), "B": _quote("5")}
    out = value_portfolio(lots, {"A": ETF, "B": BOND}, quotes)
    assert out.total_eur == Decimal("160.00")
    assert out.change_week_eur == Decimal("10.00")  # solo A: 110 − 100
    assert out.change_week_pct == Decimal("0.0667")  # 10 / 150


def test_positions_sorted_by_value() -> None:
    lots = [LotIn("A", T0, Decimal("1"), Decimal("1")), LotIn("B", T0, Decimal("1"), Decimal("1"))]
    out = value_portfolio(lots, {"A": ETF, "B": BOND}, {"A": _quote("1"), "B": _quote("2")})
    assert [p.asset_id for p in out.positions] == ["B", "A"]
