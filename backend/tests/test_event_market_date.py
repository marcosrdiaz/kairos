"""Fecha real del evento y movimiento observado en `EventImpactOut` (T2-22).

La gráfica de evolución sitúa cada evento en su día de mercado (`market_date`), no en la hora del
replay (`occurred_at`), y su tarjeta muestra el movimiento de cada factor (`factor_moves`).
"""

from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.agents import analyzer
from app.core import clock
from app.core.errors import AppError, ErrorCode
from app.events import service
from app.main import API_PREFIX

NOW = datetime(2026, 11, 8, 18, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _clock() -> Iterator[None]:
    clock.set_now(NOW)
    yield
    analyzer.set_client(None)


def test_market_date_is_the_date_in_the_replay_json() -> None:
    assert service.get_market_date("oil-2025-06") == datetime(2025, 6, 13, 1, 42, tzinfo=UTC)


def test_market_date_ignores_the_replay_time(client: TestClient) -> None:
    client.post(f"{API_PREFIX}/demo/replay/oil-2025-06")
    assert service.get_event("oil-2025-06").occurred_at == NOW  # la app lo muestra hoy
    assert service.get_market_date("oil-2025-06").date().isoformat() == "2025-06-13"


def test_events_carry_market_date_and_observed_factor_moves(client: TestClient) -> None:
    client.post(f"{API_PREFIX}/demo/replay/bce-2025-06")
    event = client.get(f"{API_PREFIX}/portfolios/laura/events").json()[0]
    assert event["occurred_at"] == "2026-11-08T18:00:00Z"
    assert event["market_date"].startswith("2025-06-05")
    moves = {k: Decimal(v) for k, v in event["factor_moves"].items()}
    # Sin analizador, el ShockSet lleva todos los factores observados del JSON.
    assert moves == {
        "EQ_GLOBAL": Decimal("0.00085"),
        "EQ_US_TECH": Decimal("-0.00803"),
        "OIL": Decimal("0.00740"),
        "EURUSD": Decimal("0.00330"),
        "RATES_EUR": Decimal("0.00024"),
    }


def test_unknown_event_has_no_market_date() -> None:
    with pytest.raises(AppError) as error:
        service.get_market_date("no-existe")
    assert error.value.code == ErrorCode.NOT_FOUND
