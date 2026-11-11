"""`POST /demo/reset` deja los avisos como al empezar: sin los de evento ni los que no tienen (TD-13)."""

from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event as sa_event
from sqlalchemy import text

from app.alerts import engine, repository
from app.core import clock
from app.core.db import get_engine, session_scope
from app.events import service as events_service
from app.main import API_PREFIX
from app.schemas.alerts import AlertKind

NOW = datetime(2026, 11, 8, 18, 0, tzinfo=UTC)
BIG = "nvda-2025-02"  # Laura: aviso `event_impact` (ver `test_alerts_service.py`)


@pytest.fixture(autouse=True)
def _clock() -> None:
    clock.set_now(NOW)


@pytest.fixture
def foreign_keys_on() -> Iterator[None]:
    """SQLite ignora las claves foráneas salvo con el PRAGMA; Postgres siempre las aplica."""

    @sa_event.listens_for(get_engine(), "connect")
    def _enable(dbapi_connection: Any, _: Any) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    get_engine().dispose()
    yield


def _count() -> int:
    with session_scope() as session:
        return int(session.execute(text("SELECT COUNT(*) FROM alert")).scalar() or 0)


def _save_without_event(portfolio_id: str, kind: AlertKind) -> None:
    repository.save(
        portfolio_id, None, kind, engine.score(Decimal("1"), Decimal("1")), "Aviso de prueba.", NOW
    )


def test_reset_deletes_news_and_market_move_alerts(client: TestClient, foreign_keys_on: None) -> None:
    _save_without_event("laura", AlertKind.NEWS_ESTIMATE)
    _save_without_event("laura", AlertKind.MARKET_MOVE)
    _save_without_event("javier", AlertKind.MARKET_MOVE)
    events_service.replay(BIG)  # además, el de evento
    assert _count() >= 4

    assert client.post(f"{API_PREFIX}/demo/reset").status_code == 200

    assert _count() == 0
    for portfolio_id in ("laura", "javier"):
        response = client.get(f"{API_PREFIX}/portfolios/{portfolio_id}/alerts")
        assert response.status_code == 200
        assert response.json() == []


def test_reset_twice_leaves_the_same_state(client: TestClient, foreign_keys_on: None) -> None:
    _save_without_event("laura", AlertKind.NEWS_ESTIMATE)
    for _ in range(2):
        assert client.post(f"{API_PREFIX}/demo/reset").status_code == 200
        assert _count() == 0
