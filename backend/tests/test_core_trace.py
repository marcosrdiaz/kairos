from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.core import clock, trace
from app.schemas.common import SourceKind, SourceRef, TraceKind


@pytest.mark.usefixtures("db")
def test_record_and_get_roundtrip() -> None:
    clock.set_now(datetime(2026, 11, 8, 18, 0, tzinfo=UTC))
    source = SourceRef(
        kind=SourceKind.EVENT,
        label="Evento de prueba",
        ref="evento-prueba",
        as_of=datetime(2026, 11, 8, tzinfo=UTC),
    )
    parent = trace.record(TraceKind.VALUATION, "V = Σ u·p", {}, {"total_eur": Decimal("1")}, [])

    calc_id = trace.record(
        TraceKind.EVENT_IMPACT,
        "I = V·β·s",
        inputs={"shocks": {"RATES_EUR": Decimal("-0.0010")}},
        outputs={"impact_eur": Decimal("90.00")},
        sources=[source],
        parent_calc_ids=[parent],
    )

    assert calc_id.startswith("calc_")
    assert len(calc_id) == len("calc_") + 32
    stored = trace.get(calc_id)
    assert stored is not None
    assert stored.kind == "event_impact"
    assert stored.inputs == {"shocks": {"RATES_EUR": "-0.0010"}}
    assert stored.outputs == {"impact_eur": "90.00"}
    assert stored.sources[0]["as_of"] == "2026-11-08T00:00:00Z"
    assert stored.parent_calc_ids == [parent]
    assert stored.created_at.replace(tzinfo=UTC) == clock.now()


@pytest.mark.usefixtures("db")
def test_get_unknown_returns_none() -> None:
    assert trace.get("calc_" + "0" * 32) is None


@pytest.mark.usefixtures("db")
def test_record_rejects_unknown_kind() -> None:
    with pytest.raises(ValueError):
        trace.record("invented", "", {}, {}, [])
