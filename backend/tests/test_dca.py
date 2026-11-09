"""Planes DCA (T1-06, RF-07, UC-04): calendario, alta, edición y validación del reparto.

Reloj fijo en el domingo 2026-11-08 18:00 UTC. Laura: 300 € al mes el día 5, 70/30 entre
IE00B03HD191 e IE00B18GC888. Javier: 200 € al mes el día 10. Las ejecuciones están en
`test_dca_executions.py`.
"""

import json
from collections.abc import Iterator
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core import clock
from app.core.errors import AppError, ErrorCode
from app.main import API_PREFIX
from app.portfolio import dca, service
from app.schemas.portfolio import (
    DcaAllocation,
    DcaPlanCreateRequest,
    DcaPlanStatus,
    DcaPlanUpdateRequest,
    Frequency,
)
from tests.fakes.price_provider import FakePriceProvider, use_price_provider

PRICES: dict[str, Any] = json.loads(
    (Path(__file__).parent / "golden" / "portfolio_init_cases.json").read_text(encoding="utf-8")
)
NOW = datetime.fromisoformat(PRICES["now"])  # 2026-11-08T18:00:00Z
MSCI_EUR, BONDS, EUROSTOXX = "IE00B03HD191", "IE00B18GC888", "IE0007472115"


@pytest.fixture(autouse=True)
def _prices() -> Iterator[None]:
    clock.set_now(NOW)
    with use_price_provider(FakePriceProvider(closes=PRICES["closes"], fx=PRICES["fx"])):
        yield


@pytest.fixture
def seeded(db: None) -> None:
    service.load_seed(force=True)


def _alloc(*pairs: tuple[str, str]) -> list[DcaAllocation]:
    return [DcaAllocation(asset_id=a, weight=Decimal(w)) for a, w in pairs]


def _error(exc: pytest.ExceptionInfo[AppError]) -> ErrorCode:
    return exc.value.code


# --- Calendario (puro) ---


@pytest.mark.parametrize(
    ("frequency", "day", "after", "inclusive", "expected"),
    [
        (Frequency.MONTHLY, 5, datetime(2026, 12, 5, 9, tzinfo=UTC), False, date(2027, 1, 5)),
        (Frequency.MONTHLY, 5, datetime(2026, 12, 5, 9, tzinfo=UTC), True, date(2026, 12, 5)),
        (Frequency.MONTHLY, 28, datetime(2027, 1, 30, tzinfo=UTC), True, date(2027, 2, 28)),
        (Frequency.WEEKLY, 7, datetime(2026, 11, 8, tzinfo=UTC), False, date(2026, 11, 15)),
        (Frequency.WEEKLY, 5, datetime(2026, 12, 31, 23, tzinfo=UTC), True, date(2027, 1, 1)),
    ],
)
def test_next_execution(
    frequency: Frequency, day: int, after: datetime, inclusive: bool, expected: date
) -> None:
    found = dca.next_execution(frequency, day, after, inclusive=inclusive)
    assert found == datetime(expected.year, expected.month, expected.day, tzinfo=UTC)


# --- Planes ---


def test_seed_plans_are_listed(seeded: None) -> None:
    (plan,) = service.list_dca_plans("laura")
    assert plan.model_dump(mode="json") == {
        "id": "dca_laura",
        "portfolio_id": "laura",
        "amount_eur": "300.00",
        "frequency": "monthly",
        "day": 5,
        "status": "active",
        "allocations": [
            {"asset_id": MSCI_EUR, "weight": "0.7"},
            {"asset_id": BONDS, "weight": "0.3"},
        ],
        "last_execution_at": "2026-10-05T00:00:00Z",
        "next_execution_at": "2026-12-05T00:00:00Z",
    }


def test_list_plans_unknown_portfolio(seeded: None) -> None:
    with pytest.raises(AppError) as exc:
        service.list_dca_plans("nadie")
    assert _error(exc) is ErrorCode.NOT_FOUND


@pytest.mark.parametrize(
    ("frequency", "day", "next_at"),
    [
        (Frequency.MONTHLY, 8, datetime(2026, 11, 8, tzinfo=UTC)),  # hoy cuenta
        (Frequency.MONTHLY, 5, datetime(2026, 12, 5, tzinfo=UTC)),
        (Frequency.MONTHLY, 20, datetime(2026, 11, 20, tzinfo=UTC)),
        (Frequency.WEEKLY, 7, datetime(2026, 11, 8, tzinfo=UTC)),  # el 8 es domingo
        (Frequency.WEEKLY, 1, datetime(2026, 11, 9, tzinfo=UTC)),
        (Frequency.WEEKLY, 3, datetime(2026, 11, 11, tzinfo=UTC)),
    ],
)
def test_create_plan_computes_next_execution(
    seeded: None, frequency: Frequency, day: int, next_at: datetime
) -> None:
    request = DcaPlanCreateRequest(
        amount_eur=Decimal("150.00"),
        frequency=frequency,
        day=day,
        allocations=_alloc((EUROSTOXX, "0.5"), (BONDS, "0.5")),
    )
    plan = service.create_dca_plan("laura", request)
    assert plan.id.startswith("dca_")
    assert plan.portfolio_id == "laura"
    assert plan.status is DcaPlanStatus.ACTIVE
    assert plan.last_execution_at is None
    assert plan.next_execution_at == next_at
    assert plan in service.list_dca_plans("laura")


@pytest.mark.parametrize(
    "allocations",
    [
        _alloc((MSCI_EUR, "0.70"), (BONDS, "0.29")),
        _alloc((MSCI_EUR, "0.70"), (BONDS, "0.31")),
        _alloc((MSCI_EUR, "0.5"), (MSCI_EUR, "0.5")),
        _alloc((MSCI_EUR, "1.2"), (BONDS, "-0.2")),
        _alloc((MSCI_EUR, "1"), (BONDS, "0")),
    ],
    ids=["sum-below-1", "sum-above-1", "duplicate-asset", "negative-weight", "zero-weight"],
)
def test_create_plan_rejects_invalid_allocations(
    seeded: None, allocations: list[DcaAllocation]
) -> None:
    request = DcaPlanCreateRequest(
        amount_eur=Decimal("100.00"), frequency=Frequency.MONTHLY, day=1, allocations=allocations
    )
    with pytest.raises(AppError) as exc:
        service.create_dca_plan("laura", request)
    assert _error(exc) is ErrorCode.DCA_ALLOCATION_INVALID
    assert len(service.list_dca_plans("laura")) == 1


def test_create_plan_unknown_asset_or_portfolio(seeded: None) -> None:
    request = DcaPlanCreateRequest(
        amount_eur=Decimal("100.00"),
        frequency=Frequency.MONTHLY,
        day=1,
        allocations=_alloc(("XX0000000000", "1")),
    )
    with pytest.raises(AppError) as exc:
        service.create_dca_plan("laura", request)
    assert _error(exc) is ErrorCode.NOT_FOUND
    with pytest.raises(AppError) as exc:
        service.create_dca_plan("nadie", request)
    assert _error(exc) is ErrorCode.NOT_FOUND


def test_create_weekly_plan_rejects_day_beyond_sunday(seeded: None) -> None:
    request = DcaPlanCreateRequest(
        amount_eur=Decimal("50.00"),
        frequency=Frequency.WEEKLY,
        day=8,
        allocations=_alloc((MSCI_EUR, "1")),
    )
    with pytest.raises(AppError) as exc:
        service.create_dca_plan("laura", request)
    assert _error(exc) is ErrorCode.VALIDATION_ERROR


def test_update_plan_pauses_and_changes_amount(seeded: None) -> None:
    request = DcaPlanUpdateRequest(status=DcaPlanStatus.PAUSED, amount_eur=Decimal("250.00"))
    plan = service.update_dca_plan("laura", "dca_laura", request)
    assert plan.status is DcaPlanStatus.PAUSED
    assert plan.amount_eur == Decimal("250.00")
    assert plan.next_execution_at == datetime(2026, 12, 5, tzinfo=UTC)  # sin cambio de día
    assert service.list_dca_plans("laura") == [plan]


def test_update_plan_day_recomputes_next_execution(seeded: None) -> None:
    plan = service.update_dca_plan("laura", "dca_laura", DcaPlanUpdateRequest(day=20))
    assert plan.day == 20
    assert plan.next_execution_at == datetime(2026, 11, 20, tzinfo=UTC)
    assert plan.last_execution_at == datetime(2026, 10, 5, tzinfo=UTC)


def test_update_plan_replaces_allocations(seeded: None) -> None:
    request = DcaPlanUpdateRequest(allocations=_alloc((BONDS, "0.6"), (MSCI_EUR, "0.4")))
    plan = service.update_dca_plan("laura", "dca_laura", request)
    assert [(a.asset_id, a.weight) for a in plan.allocations] == [
        (BONDS, Decimal("0.6")),
        (MSCI_EUR, Decimal("0.4")),
    ]


def test_update_plan_rejects_invalid_allocations(seeded: None) -> None:
    request = DcaPlanUpdateRequest(allocations=_alloc((BONDS, "0.6")))
    with pytest.raises(AppError) as exc:
        service.update_dca_plan("laura", "dca_laura", request)
    assert _error(exc) is ErrorCode.DCA_ALLOCATION_INVALID
    (plan,) = service.list_dca_plans("laura")
    assert len(plan.allocations) == 2


@pytest.mark.parametrize(("portfolio_id", "plan_id"), [("laura", "dca_x"), ("javier", "dca_laura")])
def test_update_plan_not_found(seeded: None, portfolio_id: str, plan_id: str) -> None:
    with pytest.raises(AppError) as exc:
        service.update_dca_plan(portfolio_id, plan_id, DcaPlanUpdateRequest(day=3))
    assert _error(exc) is ErrorCode.NOT_FOUND


# --- API ---


def test_api_create_and_patch_plan(client: TestClient) -> None:
    body = {
        "amount_eur": "120.00",
        "frequency": "monthly",
        "day": 15,
        "allocations": [{"asset_id": MSCI_EUR, "weight": "1"}],
    }
    created = client.post(f"{API_PREFIX}/portfolios/laura/dca-plans", json=body)
    assert created.status_code == 201
    plan_id = created.json()["id"]
    patched = client.patch(
        f"{API_PREFIX}/portfolios/laura/dca-plans/{plan_id}", json={"status": "paused"}
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "paused"
    invalid = client.post(
        f"{API_PREFIX}/portfolios/laura/dca-plans",
        json={**body, "allocations": [{"asset_id": MSCI_EUR, "weight": "0.9"}]},
    )
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "DCA_ALLOCATION_INVALID"
