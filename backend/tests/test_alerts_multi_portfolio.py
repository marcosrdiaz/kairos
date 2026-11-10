"""Avisos con varias carteras (T4-15): el límite semanal de D-032 es por cartera, no en total.

Tres carteras (Laura, Javier y una tercera con NVIDIA): un evento genera como mucho un aviso por
cartera a la que mueve lo bastante, y agotar el cupo de una no quita el de las demás.
"""

from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.alerts import engine, repository
from app.core import clock
from app.events import service as events_service
from app.main import API_PREFIX
from app.schemas.alerts import AlertKind

NOW = datetime(2026, 11, 8, 18, 0, tzinfo=UTC)  # domingo: semana ISO del 2 al 8
BIG = "nvda-2025-02"  # mueve a Laura y a una cartera concentrada en NVIDIA; a Javier, no
CSV = "asset;units;avg_cost_eur\nNVDA;40;100\n"


@pytest.fixture(autouse=True)
def _clock() -> Iterator[None]:
    clock.set_now(NOW)
    yield


def _create_third(client: TestClient) -> str:
    body = {"name": "Hijos", "kind": "family", "risk_profile": "conservador", "csv": CSV}
    response = client.post(f"{API_PREFIX}/portfolios/import", json=body)
    assert response.status_code == 201, response.text
    portfolio_id: str = response.json()["portfolio"]["id"]
    # Con plan: hoy el replay falla si alguna cartera no lo tiene (`impact` pide el objetivo).
    plan = {"target": {"equity": "1", "fixed_income": "0", "cash": "0"}}
    response = client.put(f"{API_PREFIX}/portfolios/{portfolio_id}/plan", json=plan)
    assert response.status_code == 200, response.text
    return portfolio_id


def _alerts(client: TestClient, portfolio_id: str) -> list[dict[str, Any]]:
    response = client.get(f"{API_PREFIX}/portfolios/{portfolio_id}/alerts")
    assert response.status_code == 200
    body: list[dict[str, Any]] = response.json()
    return body


def _fill_week(portfolio_id: str) -> None:
    for _ in range(2):
        repository.save(
            portfolio_id,
            None,
            AlertKind.EVENT_IMPACT,
            engine.score(Decimal("1"), Decimal("1")),
            "Aviso de relleno.",
            clock.now(),
        )


def test_one_event_alerts_each_portfolio_it_moves_once(client: TestClient) -> None:
    third = _create_third(client)
    events_service.replay(BIG)
    events_service.replay(BIG)  # repetir no duplica en ninguna cartera
    assert [a["event_id"] for a in _alerts(client, "laura")] == [BIG]
    assert [a["event_id"] for a in _alerts(client, third)] == [BIG]
    assert _alerts(client, "javier") == []


def test_a_full_week_in_one_portfolio_does_not_block_the_others(client: TestClient) -> None:
    third = _create_third(client)
    _fill_week("laura")
    events_service.replay(BIG)
    assert [a["message"] for a in _alerts(client, "laura")] == ["Aviso de relleno."] * 2
    assert [a["event_id"] for a in _alerts(client, third)] == [BIG]
