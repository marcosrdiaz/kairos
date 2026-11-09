"""`GET /traces/{calc_id}` (T2-01, RF-19): de dónde sale cualquier cifra."""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core import clock, trace
from app.core.errors import ErrorCode
from app.schemas.common import ErrorOut, SourceKind, SourceRef, TraceKind
from app.schemas.portfolio import TraceOut

NOW = datetime(2026, 11, 9, 10, 30, tzinfo=UTC)
UNKNOWN = "calc_" + "0" * 32
# El mismo instante (10:30 UTC) tal como lo devolvería cada motor de BD:
SQLITE_STYLE = datetime(2026, 11, 9, 10, 30)  # noqa: DTZ001  (SQLite no guarda la zona)
POSTGRES_STYLE = datetime(2026, 11, 9, 11, 30, tzinfo=timezone(timedelta(hours=1)))  # timestamptz


def _source(label: str = "Evento de prueba") -> SourceRef:
    return SourceRef(
        kind=SourceKind.EVENT,
        label=label,
        ref="evento-prueba",
        as_of=datetime(2026, 11, 8, tzinfo=UTC),
        url="https://example.com/evento",
    )


def _record(
    kind: TraceKind = TraceKind.VALUATION,
    parents: list[str] | None = None,
    sources: list[SourceRef] | None = None,
) -> str:
    return trace.record(
        kind,
        "x = Σ y",
        inputs={"y": [Decimal("1.50"), Decimal("2.50")]},
        outputs={"x": Decimal("4.00")},
        sources=[_source()] if sources is None else sources,
        parent_calc_ids=parents,
    )


def test_trace_complete(client: TestClient) -> None:
    """Entradas, fórmula, resultado, fuentes y fecha de una cifra (plan de pruebas RF-19)."""
    clock.set_now(NOW)
    parent = _record(TraceKind.VALUATION)
    calc_id = _record(TraceKind.EVENT_IMPACT, parents=[parent])

    response = client.get(f"/api/v1/traces/{calc_id}")

    assert response.status_code == 200
    body = response.json()
    out = TraceOut.model_validate(body)  # cumple el contrato
    assert out.calc_id == calc_id
    assert out.kind is TraceKind.EVENT_IMPACT
    assert out.created_at == NOW and body["created_at"] == "2026-11-09T10:30:00Z"
    assert out.formula == "x = Σ y"
    assert body["inputs"] == {"y": ["1.50", "2.50"]}  # los Decimal viajan como string
    assert body["outputs"] == {"x": "4.00"}
    assert body["sources"] == [
        {
            "kind": "event",
            "label": "Evento de prueba",
            "ref": "evento-prueba",
            "as_of": "2026-11-08T00:00:00Z",
            "url": "https://example.com/evento",
        }
    ]
    assert body["parent_calc_ids"] == [parent]


def test_parent_chain_can_be_walked_through_the_endpoint(client: TestClient) -> None:
    """Una cifra derivada de varias trazas: se sigue `parent_calc_ids` hasta la raíz."""
    prices = _record(TraceKind.VALUATION)
    exposure = _record(TraceKind.EXPOSURE, parents=[prices])
    impact = _record(TraceKind.EVENT_IMPACT, parents=[exposure, prices])

    pending, kinds = [impact], []
    seen: set[str] = set()
    while pending:
        current = pending.pop(0)
        if current in seen:
            continue
        seen.add(current)
        body = client.get(f"/api/v1/traces/{current}").json()
        kinds.append(body["kind"])
        pending.extend(body["parent_calc_ids"])

    assert kinds == ["event_impact", "exposure", "valuation"]


def test_trace_without_sources_or_parents_returns_empty_lists(client: TestClient) -> None:
    calc_id = _record(sources=[])
    body = client.get(f"/api/v1/traces/{calc_id}").json()
    assert body["sources"] == [] and body["parent_calc_ids"] == []


def test_dangling_parent_ids_are_returned_as_they_are(client: TestClient) -> None:
    """Un padre que no existe (p. ej. el `calc_id` de un mock) no rompe la traza hija."""
    calc_id = _record(parents=[UNKNOWN])
    response = client.get(f"/api/v1/traces/{calc_id}")
    assert response.status_code == 200
    assert response.json()["parent_calc_ids"] == [UNKNOWN]
    assert client.get(f"/api/v1/traces/{UNKNOWN}").status_code == 404


@pytest.mark.parametrize("kind", list(TraceKind))
def test_every_trace_kind_is_served(client: TestClient, kind: TraceKind) -> None:
    calc_id = _record(kind)
    response = client.get(f"/api/v1/traces/{calc_id}")
    assert response.status_code == 200
    assert response.json()["kind"] == kind.value


@pytest.mark.parametrize("calc_id", [UNKNOWN, "nope", "calc_", "calc_xyz", "0" * 40])
def test_unknown_trace_is_a_404_with_the_standard_error_body(
    client: TestClient, calc_id: str
) -> None:
    response = client.get(f"/api/v1/traces/{calc_id}")
    assert response.status_code == 404
    error = ErrorOut.model_validate(response.json())
    assert error.code == ErrorCode.NOT_FOUND.value
    assert error.details == {"calc_id": calc_id}


@pytest.mark.usefixtures("db")
def test_get_returns_a_timezone_aware_utc_datetime() -> None:
    """SQLite (BD real de los tests) devuelve la fecha sin zona; `TraceOut` exige zona."""
    clock.set_now(NOW)
    stored = trace.get(_record())
    assert stored is not None
    assert stored.created_at.tzinfo is not None
    assert stored.created_at == NOW


def _row_with(created_at: datetime) -> trace.CalcTrace:
    return trace.CalcTrace(
        id=UNKNOWN,
        kind="valuation",
        formula="x = Σ y",
        inputs={},
        outputs={"x": "4.00"},
        sources=[],
        parent_calc_ids=[],
        created_at=created_at,
    )


def _engine_returns(monkeypatch: pytest.MonkeyPatch, row: trace.CalcTrace) -> None:
    """Hace que `trace.get` lea `row` tal cual, como lo devolvería el motor de BD."""

    class _Session:
        def get(self, model: object, key: str) -> trace.CalcTrace:
            return row

    @contextmanager
    def fake_session_scope() -> Iterator[_Session]:
        yield _Session()

    monkeypatch.setattr(trace, "session_scope", fake_session_scope)


def test_get_leaves_a_date_with_zone_untouched_as_postgres_returns_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Postgres (`timestamptz`) devuelve la fecha con zona, a veces la de la sesión (no UTC)."""
    madrid = timezone(timedelta(hours=1))
    stored_at = datetime(2026, 11, 9, 11, 30, tzinfo=madrid)  # = 10:30 UTC
    _engine_returns(monkeypatch, _row_with(stored_at))

    stored = trace.get(UNKNOWN)

    assert stored is not None
    assert stored.created_at is stored_at  # ni se copia ni se convierte
    assert stored.created_at.utcoffset() == timedelta(hours=1)
    assert stored.created_at == NOW  # el instante es el mismo


def test_get_assumes_utc_for_a_date_without_zone_as_sqlite_returns_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _engine_returns(monkeypatch, _row_with(SQLITE_STYLE))

    stored = trace.get(UNKNOWN)

    assert stored is not None
    assert stored.created_at.tzinfo is UTC
    assert stored.created_at == NOW  # misma hora de reloj, ahora en UTC


@pytest.mark.parametrize(
    "created_at",
    [SQLITE_STYLE, POSTGRES_STYLE],
    ids=["sin-zona (sqlite)", "con-zona (postgres)"],
)
def test_endpoint_serves_the_same_instant_with_either_engine(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, created_at: datetime
) -> None:
    _engine_returns(monkeypatch, _row_with(created_at))
    response = client.get(f"/api/v1/traces/{UNKNOWN}")
    assert response.status_code == 200
    assert response.json()["created_at"] == "2026-11-09T10:30:00Z"


def test_endpoint_is_documented_in_openapi(client: TestClient) -> None:
    operation = client.get("/openapi.json").json()["paths"]["/api/v1/traces/{calc_id}"]["get"]
    responses = operation["responses"]
    assert responses["200"]["content"]["application/json"]["schema"]["$ref"].endswith("/TraceOut")
    assert responses["404"]["content"]["application/json"]["schema"]["$ref"].endswith("/ErrorOut")
