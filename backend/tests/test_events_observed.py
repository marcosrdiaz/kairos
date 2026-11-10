"""Shock medido de forma automática (T4-04, D-089).

- `events/observed.py`: la lógica de `scripts/fetch_prices.py` (cierre de la sesión que recoge el
  evento frente al cierre anterior), pura y compartida por el script y el backend.
- Un evento sin `observed` cuya sesión aún no ha cerrado queda **pendiente de cierre**: se guarda
  con su análisis y sin cifras. Tras el cierre, `process_pending` mide el shock y lo procesa.
"""

import importlib.util
import json
import sys
from collections.abc import Iterator
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from types import ModuleType

import pytest
from fastapi.testclient import TestClient

from app.core import clock
from app.events import observed, service
from app.impact import service as impact_service
from app.main import API_PREFIX
from app.prices import service as prices_service
from app.prices.provider import PricePoint
from app.schemas.common import Factor
from app.schemas.events import EventIn, EventObserved

PENDING_URL = f"{API_PREFIX}/events/pending"
ROOT = Path(__file__).resolve().parents[2]
REPLAY = ROOT / "data" / "events" / "replay"
NVDA = {"NVDA": "US67066G1040"}
TUE = date(2026, 11, 10)


def _replay(event_id: str) -> EventIn:
    return EventIn.model_validate(json.loads((REPLAY / f"{event_id}.json").read_text("utf-8")))


# --- Lógica pura ---


@pytest.mark.parametrize(
    ("occurred_at", "expected"),
    [
        (datetime(2025, 6, 5, 12, 15, tzinfo=UTC), date(2025, 6, 5)),
        (datetime(2025, 2, 26, 21, 20, tzinfo=UTC), date(2025, 2, 27)),  # tras el cierre de EE. UU.
    ],
)
def test_reaction_date(occurred_at: datetime, expected: date) -> None:
    assert observed.reaction_date(occurred_at) == expected


def test_measure_is_relative_except_rates_and_rounds_to_5_decimals() -> None:
    series = [(date(2026, 11, 6), Decimal("100")), (date(2026, 11, 9), Decimal("101.234567"))]
    rates = [(date(2026, 11, 6), Decimal("0.0262")), (date(2026, 11, 9), Decimal("0.026446"))]
    factors = {f: (rates if f is Factor.RATES_EUR else series) for f in Factor}

    result = observed.measure(date(2026, 11, 9), factors, {"NVDA": series})

    assert result is not None
    assert result.factors[Factor.EQ_GLOBAL] == Decimal("0.01235")
    assert result.factors[Factor.RATES_EUR] == Decimal("0.00025")
    assert result.companies == {"NVDA": Decimal("0.01235")}


def test_measure_is_pending_until_the_reaction_session_has_closed() -> None:
    before = [(date(2026, 11, 6), Decimal("100")), (date(2026, 11, 9), Decimal("101"))]
    factors = {f: before for f in Factor}

    assert observed.measure(TUE, factors, {}) is None
    partial = {**factors, Factor.OIL: [*before, (TUE, Decimal("102"))]}
    assert observed.measure(TUE, partial, {}) is None  # todos los factores o ninguno


def test_weekend_event_takes_monday_session() -> None:
    series = [(date(2026, 11, 6), Decimal("100")), (date(2026, 11, 9), Decimal("99"))]
    result = observed.measure(date(2026, 11, 7), {f: series for f in Factor}, {})
    assert result is not None
    assert result.factors[Factor.OIL] == Decimal("-0.01000")


# --- Mismo resultado que `fetch_prices.py --observed-only` ---


@pytest.fixture
def fetch_prices() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "fetch_prices", ROOT / "scripts" / "fetch_prices.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["fetch_prices"] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("event_id", ["bce-2025-06", "oil-2025-06", "nvda-2025-02"])
def test_backend_measures_the_same_as_the_replay_json(
    event_id: str, fetch_prices: ModuleType
) -> None:
    clock.set_now(datetime(2026, 11, 10, tzinfo=UTC))
    event = _replay(event_id)
    companies = NVDA if event_id == "nvda-2025-02" else {}

    measured = service.measure_observed(event.model_copy(update={"observed": None}), companies)

    assert measured == event.observed
    script = fetch_prices.compute_observed(
        json.loads((REPLAY / f"{event_id}.json").read_text("utf-8"))
    )
    assert EventObserved.model_validate(script) == event.observed


# --- Pendiente de cierre ---


class GrowingFactors:
    """Factores con cierres hasta el lunes; `close_tuesday()` añade el cierre del martes."""

    def __init__(self) -> None:
        self.days = [(date(2026, 11, 6), Decimal("100")), (date(2026, 11, 9), Decimal("100"))]

    def close_tuesday(self) -> None:
        self.days.append((TUE, Decimal("103")))

    def factor_closes(self, factor: Factor) -> list[PricePoint]:
        return [PricePoint(day=d, value=v) for d, v in self.days]

    def source_of(self, factor: Factor, day: date) -> str | None:
        return "yahoo:test"


@pytest.fixture
def growing(client: TestClient) -> Iterator[GrowingFactors]:
    clock.set_now(datetime(2026, 11, 10, 15, 0, tzinfo=UTC))
    source = GrowingFactors()
    previous = prices_service.set_factor_source(source)
    yield source
    prices_service.set_factor_source(previous)


def _today_event() -> EventIn:
    return EventIn(
        id="opec-2026-11-10",
        type=_replay("oil-2025-06").type,
        title="La OPEP+ anuncia un recorte de producción",
        occurred_at=datetime(2026, 11, 10, 13, 0, tzinfo=UTC),
        text="La OPEP+ recorta su producción a partir de diciembre.",
        source_urls=["https://example.org/opep"],
        fallback_chain=["La OPEP+ recorta la producción.", "El crudo tiende a subir."],
        illustrative=False,
    )


def test_event_before_the_close_is_pending_without_figures(growing: GrowingFactors) -> None:
    result = service.ingest(_today_event())

    assert result is None
    assert service.list_pending() == ["opec-2026-11-10"]
    assert impact_service.list_event_impacts("laura", 30) == []
    analysis = service.get_analysis("opec-2026-11-10")
    assert analysis is not None
    assert analysis.causal_chain  # la cadena causal sí se ve
    assert analysis.channels == []  # sin dirección inventada: no hay movimiento observado


def test_after_the_close_the_pending_event_gets_impact_range_and_calc_id(
    growing: GrowingFactors,
) -> None:
    service.ingest(_today_event())
    assert service.process_pending() == []  # aún sin el cierre del martes

    growing.close_tuesday()
    assert service.process_pending() == []  # la sesión de hoy nunca se da por cerrada

    clock.set_now(datetime(2026, 11, 11, 22, 30, tzinfo=UTC))  # al día siguiente
    processed = service.process_pending()

    assert processed == ["opec-2026-11-10"]
    assert service.list_pending() == []
    impacts = [
        i for i in impact_service.list_event_impacts("laura", 30) if i.event_id == "opec-2026-11-10"
    ]
    [impact] = impacts
    assert impact.calc_id
    assert impact.low_eur <= impact.impact_eur <= impact.high_eur


def test_event_with_its_session_already_closed_is_processed_at_once(
    growing: GrowingFactors,
) -> None:
    monday = _today_event().model_copy(
        update={"occurred_at": datetime(2026, 11, 9, 13, 0, tzinfo=UTC)}
    )
    result = service.ingest(monday)

    assert result is not None
    assert "laura" in result.portfolios
    assert service.list_pending() == []


def test_route_shows_the_pending_event_with_its_chain_and_no_figures(
    growing: GrowingFactors, client: TestClient
) -> None:
    assert client.get(PENDING_URL).json() == []
    service.ingest(_today_event())

    [event] = client.get(PENDING_URL).json()

    assert event["event_id"] == "opec-2026-11-10"
    assert event["status"] == "pending_close"
    assert event["causal_chain"] == _today_event().fallback_chain  # respaldo: sin clave de Claude
    assert event["occurred_at"] == "2026-11-10T13:00:00Z"
    assert [s["url"] for s in event["sources"]] == ["https://example.org/opep"]
    assert not {"impact_eur", "low_eur", "high_eur", "calc_id"} & set(event)


def test_route_drops_the_event_once_it_has_figures(
    growing: GrowingFactors, client: TestClient
) -> None:
    service.ingest(_today_event())
    growing.close_tuesday()
    clock.set_now(datetime(2026, 11, 11, 22, 30, tzinfo=UTC))
    service.process_pending()

    assert client.get(PENDING_URL).json() == []
    events = client.get(f"{API_PREFIX}/portfolios/laura/events").json()
    assert "opec-2026-11-10" in [e["event_id"] for e in events]


def test_reset_also_forgets_pending_events(growing: GrowingFactors) -> None:
    service.ingest(_today_event())
    impact_service.reset()
    service.reset()
    assert service.list_pending() == []
