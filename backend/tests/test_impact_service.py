"""`impact/service.py`: impacto real por la interfaz pública, persistencia, traza y API."""

import json
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core import clock, trace
from app.core.db import session_scope
from app.core.errors import AppError
from app.events.models import Event
from app.impact import repository, service
from app.impact.betas import BetaEstimate
from app.main import API_PREFIX
from app.portfolio import service as portfolio_service
from app.schemas.agents import ExplanationStatus
from app.schemas.common import Factor, SourceKind
from app.schemas.events import (
    Channel,
    Direction,
    EventAnalysis,
    EventIn,
    EventType,
    Relevance,
    SelectedBy,
    ShockSet,
)
from app.schemas.impact import EventImpactOut

REPLAY_DIR = Path(__file__).resolve().parents[2] / "data" / "events" / "replay"
NOW = datetime(2026, 11, 8, 18, 0, tzinfo=UTC)


@pytest.fixture
def betas(client: TestClient) -> None:
    """Betas sintéticas (β 1, se 0,01, R² 0,8 a `EQ_GLOBAL`) para todos los activos con precio."""
    clock.set_now(NOW)
    ids: set[str] = set()
    for portfolio in ("laura", "javier"):
        ids |= {p.asset_id for p in portfolio_service.get_valued(portfolio).positions}
    ids -= {"DEP-12M", "PP-MIXTO"}
    repository.replace_betas(
        [
            BetaEstimate(
                asset_id=asset_id,
                factor=Factor.EQ_GLOBAL,
                beta=Decimal("1"),
                std_err=Decimal("0.01"),
                r2=Decimal("0.8"),
                n_obs=700,
                window_start=date(2023, 11, 7),
                window_end=date(2026, 11, 6),
            )
            for asset_id in ids
        ]
    )


def _event(event_id: str) -> EventIn:
    path = REPLAY_DIR / f"{event_id}.json"
    event = EventIn.model_validate(json.loads(path.read_text(encoding="utf-8")))
    with session_scope() as session:
        session.merge(
            Event(
                id=event.id,
                type=event.type.value,
                title=event.title,
                text=event.text,
                occurred_at=event.occurred_at,
                replay=True,
                source_urls=event.source_urls,
                entities=[],
                analysis=None,
                analyzed_model=None,
                created_at=clock.now(),
            )
        )
    return event


def _analysis(event: EventIn, factors: list[Factor]) -> EventAnalysis:
    return EventAnalysis(
        schema_version=1,
        event_id=event.id,
        event_type=event.type,
        entities=[],
        channels=[
            Channel(factor=f, direction=Direction.DOWN, label="bolsa mundial", rationale="Motivo")
            for f in factors
        ],
        companies=[],
        causal_chain=["Pasa algo"],
        relevance=Relevance.HIGH,
        analyzed_model="fake",
        fallback=False,
    )


def _shocks(event: EventIn, factors: list[Factor]) -> ShockSet:
    assert event.observed is not None
    return ShockSet(
        event_id=event.id,
        factor_shocks={f: event.observed.factors[f] for f in factors},
        company_moves=event.observed.companies,
        selected_by=SelectedBy.ANALYZER,
        source={"kind": SourceKind.EVENT, "label": "Observado", "ref": event.id},
    )


def _compute(event_id: str, portfolio: str = "laura") -> EventImpactOut:
    event = _event(event_id)
    factors = [Factor.EQ_GLOBAL]
    return service.compute_event_impact(
        portfolio, _analysis(event, factors), _shocks(event, factors)
    )


def test_event_impact_matches_shock_on_valued_portfolio(betas: None) -> None:
    impact = _compute("oil-2025-06")
    event = _event("oil-2025-06")
    assert event.observed is not None
    shock = event.observed.factors[Factor.EQ_GLOBAL]
    values = portfolio_service.get_valued("laura").positions
    for asset, position in zip(impact.breakdown, values, strict=True):
        assert asset.asset_id == position.asset_id
        assert abs(asset.impact_eur - position.value_eur * shock) <= Decimal("0.01")
    assert impact.impact_eur == sum(a.impact_eur for a in impact.breakdown)
    assert impact.low_eur <= impact.impact_eur <= impact.high_eur
    assert impact.explanation_status is ExplanationStatus.PENDING
    assert impact.causal_chain[0] == "Pasa algo"
    assert len(impact.causal_chain) == 2


def test_impact_is_traced_with_betas_and_shocks(betas: None) -> None:
    impact = _compute("oil-2025-06")
    record = trace.get(impact.calc_id)
    assert record is not None
    assert record.kind == "event_impact"
    assert "EQ_GLOBAL" in record.inputs["factor_shocks"]
    assert record.inputs["positions"][0]["betas"]["EQ_GLOBAL"]["beta"] == "1.00000000"
    assert record.parent_calc_ids[0].startswith("calc_")
    assert {s.kind for s in impact.sources} == {SourceKind.EVENT, SourceKind.BETA}


def test_earnings_reach_funds_through_look_through(betas: None) -> None:
    impact = _compute("nvda-2025-02")
    assert any(s.kind is SourceKind.COMPOSITION for s in impact.sources)
    assert impact.event_type == EventType.EARNINGS.value
    record = trace.get(impact.calc_id)
    assert record is not None
    weights = [p["company_weights"] for p in record.inputs["positions"]]
    assert any("NVDA" in w for w in weights)


def test_same_event_differs_between_portfolios(betas: None) -> None:
    assert _compute("nvda-2025-02").impact_eur != _compute("nvda-2025-02", "javier").impact_eur


def test_surprise_comes_from_consensus(betas: None) -> None:
    surprise = _compute("bce-2025-06").surprise
    assert surprise.label is not None and surprise.label.value == "en_linea"
    assert surprise.metric == "rate_change_bp"
    assert _compute("oil-2025-06").surprise.label is None


def test_no_betas_means_low_confidence_and_zero(client: TestClient) -> None:
    impact = _compute("oil-2025-06")
    assert impact.impact_eur == Decimal("0.00")
    assert impact.confidence.value == "baja"


def test_listed_impact_equals_computed(betas: None, client: TestClient) -> None:
    impact = _compute("oil-2025-06")
    body = client.get(f"{API_PREFIX}/portfolios/laura/events", params={"days": 7}).json()
    assert body == [impact.model_dump(mode="json")]


def test_list_honours_the_window(betas: None) -> None:
    _compute("oil-2025-06")
    clock.set_now(NOW + timedelta(days=8))
    assert service.list_event_impacts("laura", 7) == []
    assert len(service.list_event_impacts("laura", 9)) == 1


def test_recomputing_replaces_the_stored_impact(betas: None) -> None:
    _compute("oil-2025-06")
    second = _compute("oil-2025-06")
    assert [i.calc_id for i in service.list_event_impacts("laura", 7)] == [second.calc_id]


def test_attach_explanation_is_listed(betas: None) -> None:
    _compute("oil-2025-06")
    service.attach_explanation("oil-2025-06", "laura", "Texto", ExplanationStatus.OK)
    listed = service.list_event_impacts("laura", 7)[0]
    assert (listed.explanation, listed.explanation_status) == ("Texto", ExplanationStatus.OK)


def test_attach_explanation_without_impact_is_not_found(client: TestClient) -> None:
    with pytest.raises(AppError):
        service.attach_explanation("oil-2025-06", "laura", "Texto", ExplanationStatus.OK)


def test_unknown_event_is_not_found(client: TestClient) -> None:
    event = _event("oil-2025-06").model_copy(update={"id": "nada"})
    factors = [Factor.EQ_GLOBAL]
    with pytest.raises(AppError):
        service.compute_event_impact("laura", _analysis(event, factors), _shocks(event, factors))


def test_scenario_endpoint_computes_and_traces(betas: None, client: TestClient) -> None:
    total = portfolio_service.get_valued("laura")
    response = client.post(
        f"{API_PREFIX}/portfolios/laura/scenarios", json={"factor_shocks": {"EQ_GLOBAL": "-0.10"}}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["factor_shocks"] == {"EQ_GLOBAL": "-0.10"}
    priced = sum(
        (p.value_eur for p in total.positions if p.asset_id not in {"DEP-12M", "PP-MIXTO"}),
        Decimal("0"),
    )
    assert abs(Decimal(body["impact_eur"]) + priced / 10) <= Decimal("0.05")
    assert Decimal(body["low_eur"]) < Decimal(body["impact_eur"]) < Decimal(body["high_eur"])
    record = trace.get(body["calc_id"])
    assert record is not None and record.kind == "scenario"


def test_scenario_rejects_impossible_dollar_shock(client: TestClient) -> None:
    response = client.post(
        f"{API_PREFIX}/portfolios/laura/scenarios", json={"factor_shocks": {"EURUSD": "-1"}}
    )
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
