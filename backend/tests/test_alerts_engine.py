"""Reglas de los avisos: puntuación, umbral, semana ISO y sincronía con el widget (T2-08, D-032)."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.alerts import config, engine
from app.status import config as status_config
from app.status import engine as status_engine


def test_score_is_the_impact_over_the_threshold() -> None:
    assert engine.score(Decimal("-300"), Decimal("20000")) == Decimal("2")  # umbral: 150 €
    assert engine.score(Decimal("225"), Decimal("90000")) == Decimal("0.5")  # umbral: 450 €


def test_threshold_is_the_larger_of_the_floor_and_the_share() -> None:
    assert engine.threshold_eur(Decimal("10000")) == Decimal("150")
    assert engine.threshold_eur(Decimal("100000")) == Decimal("500")


@pytest.mark.parametrize(
    ("impact", "total", "expected"),
    [
        ("-150", "10000", True),  # justo en el umbral
        ("-149.99", "10000", False),
        ("500", "100000", True),
        ("-499.99", "100000", False),
        ("0", "10000", False),
    ],
)
def test_is_significant_at_the_boundary(impact: str, total: str, expected: bool) -> None:
    assert engine.is_significant(Decimal(impact), Decimal(total)) is expected


def test_thresholds_match_the_widget_config() -> None:
    """Widget «Atento» y aviso deben encenderse a la vez (paso 3 del guion). T3-04 los calibra."""
    assert config.MIN_EUR == status_config.ATENTO_MIN_EUR
    assert config.MIN_SHARE == status_config.ATENTO_MIN_SHARE


@pytest.mark.parametrize("total", ["5000", "30000", "42363.67", "100000", "180000.25"])
@pytest.mark.parametrize("impact", ["-8.38", "-149.99", "-150", "-224.86", "-899.99", "-900.13"])
def test_alert_and_widget_agree_on_every_amount(impact: str, total: str) -> None:
    value, patrimony = Decimal(impact), Decimal(total)
    assert engine.is_significant(value, patrimony) == status_engine.is_significant(value, patrimony)


def test_iso_week_runs_from_monday_to_monday() -> None:
    start, end = engine.iso_week_bounds(datetime(2026, 11, 8, 23, 59, tzinfo=UTC))  # domingo
    assert (start, end) == (
        datetime(2026, 11, 2, tzinfo=UTC),
        datetime(2026, 11, 9, tzinfo=UTC),
    )
    start, end = engine.iso_week_bounds(datetime(2026, 11, 9, 0, 0, tzinfo=UTC))  # lunes
    assert start == datetime(2026, 11, 9, tzinfo=UTC)


def test_weekly_limit_is_two() -> None:
    assert [engine.within_weekly_limit(n) for n in (0, 1, 2, 3)] == [True, True, False, False]
