"""Funciones puras de compra y venta por lotes (`portfolio/lots.py`, T1-04)."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.portfolio import lots

D = Decimal
T0 = datetime(2023, 1, 1, tzinfo=UTC)
T1 = datetime(2024, 1, 1, tzinfo=UTC)
NOW = datetime(2026, 11, 8, tzinfo=UTC)
OLD = lots.OpenLot("lot_old", T0, D(10), D("50"))
NEW = lots.OpenLot("lot_new", T1, D(5), D("80"))


def test_size_trade_by_units_rounds_amount_to_cents() -> None:
    trade = lots.size_trade(D("182.50"), D("0.86206897"), units=D(5))
    assert trade == lots.Trade(D("5.00000000"), D("786.64"), D("157.32758702"))


def test_size_trade_by_amount_keeps_requested_amount() -> None:
    trade = lots.size_trade(D("95.42"), D(1), amount_eur=D(300))
    assert trade == lots.Trade(D("3.14399497"), D("300.00"), D("95.42000000"))


def test_size_trade_needs_exactly_one() -> None:
    with pytest.raises(ValueError):
        lots.size_trade(D(1), D(1))
    with pytest.raises(ValueError):
        lots.size_trade(D(1), D(1), units=D(1), amount_eur=D(1))


def test_sell_consumes_oldest_first_whatever_the_input_order() -> None:
    sale = lots.sell_fifo([NEW, OLD], lots.size_trade(D(100), D(1), units=D(12)))
    assert [(c.lot_id, c.units) for c in sale.consumed] == [("lot_old", D(10)), ("lot_new", D(2))]
    # 1200 − (10 × 50 + 2 × 80)
    assert sale.realized_gain_eur == D("540.00")
    assert (sale.units_after, sale.avg_cost_eur_after) == (D(3), D("80.00"))
    assert sale.created == []


def test_sell_can_realize_a_loss() -> None:
    sale = lots.sell_fifo([NEW], lots.size_trade(D(60), D(1), units=D(5)))
    assert sale.realized_gain_eur == D("-100.00")
    assert (sale.units_after, sale.avg_cost_eur_after) == (D(0), D("0.00"))


def test_sell_more_than_held_raises() -> None:
    with pytest.raises(lots.InsufficientUnits) as exc:
        lots.sell_fifo([OLD, NEW], lots.size_trade(D(1), D(1), units=D("15.00000001")))
    assert (exc.value.requested, exc.value.available) == (D("15.00000001"), D(15))


def test_sell_without_lots_raises() -> None:
    with pytest.raises(lots.InsufficientUnits):
        lots.sell_fifo([], lots.size_trade(D(1), D(1), units=D(1)))


def test_buy_creates_lot_at_current_unit_cost() -> None:
    out = lots.buy([OLD], lots.size_trade(D(100), D(1), units=D(10)), NOW)
    assert out.created == [lots.OpenLot("", NOW, D("10.00000000"), D("100.00000000"))]
    assert out.consumed == [] and out.realized_gain_eur is None
    assert (out.units_after, out.avg_cost_eur_after) == (D(20), D("75.00"))
