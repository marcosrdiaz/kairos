"""`PUT /demo/clock` (diseño del MVP §4.6): fija el reloj de la demo o vuelve al real."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.core import clock

FIXED = "2026-11-08T18:00:00Z"
URL = "/api/v1/demo/clock"


def test_sets_the_clock(client: TestClient) -> None:
    response = client.put(URL, json={"now": FIXED})

    assert response.status_code == 200
    assert response.json() == {"now": FIXED}
    assert clock.now() == datetime(2026, 11, 8, 18, 0, tzinfo=UTC)


def test_null_goes_back_to_the_real_clock(client: TestClient) -> None:
    client.put(URL, json={"now": FIXED})

    response = client.put(URL, json={"now": None})

    assert response.status_code == 200
    assert response.json()["now"] != FIXED
    assert clock.now() != datetime(2026, 11, 8, 18, 0, tzinfo=UTC)


def test_null_also_overrides_demo_clock(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DEMO_CLOCK", FIXED)
    get_settings.cache_clear()

    client.put(URL, json={"now": None})

    assert clock.now() != datetime(2026, 11, 8, 18, 0, tzinfo=UTC)


def test_rejects_a_date_without_timezone(client: TestClient) -> None:
    response = client.put(URL, json={"now": "2026-11-08T18:00:00"})

    assert response.status_code == 422
    assert clock.now() != datetime(2026, 11, 8, 18, 0, tzinfo=UTC)


def test_forbidden_outside_demo_mode(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_MODE", "false")
    get_settings.cache_clear()

    response = client.put(URL, json={"now": FIXED})

    assert response.status_code == 403
    assert response.json()["code"] == "DEMO_MODE_DISABLED"
    assert clock.now() != datetime(2026, 11, 8, 18, 0, tzinfo=UTC)
