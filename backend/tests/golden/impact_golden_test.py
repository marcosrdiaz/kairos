"""Dorado del impacto (T1-10, RF-10): 3 eventos del replay × Laura y Javier.

Entradas fijas: precios de `portfolio_init_cases.json`, composiciones de `data/seed`, betas de
prueba de `impact_cases.json` (cifras redondas, no estimadas) y el `observed` de cada evento con
todos sus factores, que es lo que elige el respaldo sin LLM del analizador. Valores esperados
calculados aparte (hoja `impact_sheet.csv`). Si el motor cambia y esto no cuadra, se revisa el
dorado con el equipo: no se "ajusta".
"""

import json
from collections.abc import Iterator
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from app.core import clock
from app.core.db import session_scope
from app.events import pipeline
from app.events.models import Event
from app.exposure import service as exposure_service
from app.impact import repository, service
from app.impact.betas import BetaEstimate
from app.portfolio import service as portfolio_service
from app.schemas.common import Factor
from app.schemas.events import EventIn
from tests.fakes.price_provider import FakePriceProvider, use_price_provider

GOLDEN = Path(__file__).parent
REPLAY_DIR = GOLDEN.parents[2] / "data" / "events" / "replay"
CASES: dict[str, Any] = json.loads((GOLDEN / "impact_cases.json").read_text(encoding="utf-8"))
PRICES: dict[str, Any] = json.loads(
    (GOLDEN / "portfolio_init_cases.json").read_text(encoding="utf-8")
)
EVENTS = list(CASES["expected"])
PORTFOLIOS = ["laura", "javier"]


def _test_betas() -> list[BetaEstimate]:
    return [
        BetaEstimate(
            asset_id=asset_id,
            factor=Factor(factor),
            beta=Decimal(b["beta"]),
            std_err=Decimal(b["std_err"]),
            r2=Decimal(spec["r2"]),
            n_obs=750,
            window_start=date(2023, 11, 6),
            window_end=date(2026, 11, 6),
        )
        for asset_id, spec in CASES["betas"].items()
        for factor, b in spec["betas"].items()
    ]


@pytest.fixture(autouse=True)
def _seeded(db: None) -> Iterator[None]:
    clock.set_now(datetime.fromisoformat(CASES["now"]))
    with use_price_provider(FakePriceProvider(closes=PRICES["closes"], fx=PRICES["fx"])):
        portfolio_service.load_seed(force=True)
        exposure_service.load_compositions()
        repository.replace_betas(_test_betas())
        yield


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


def _impact(event_id: str, portfolio_id: str) -> dict[str, Any]:
    event = _event(event_id)
    analysis = pipeline.fallback_analysis(event)
    shocks = pipeline.build_shockset(analysis, event)
    out: dict[str, Any] = service.compute_event_impact(portfolio_id, analysis, shocks).model_dump(
        mode="json"
    )
    return out


@pytest.mark.parametrize("portfolio_id", PORTFOLIOS)
@pytest.mark.parametrize("event_id", EVENTS)
def test_impact_matches_golden(event_id: str, portfolio_id: str) -> None:
    out = _impact(event_id, portfolio_id)
    expected = CASES["expected"][event_id][portfolio_id]
    for field in ("impact_eur", "low_eur", "high_eur", "impact_pct", "confidence", "polarity"):
        assert out[field] == expected[field], field
    breakdown = [
        {k: a[k] for k in ("asset_id", "impact_eur", "market_eur", "fx_eur")}
        for a in out["breakdown"]
    ]
    assert breakdown == expected["breakdown"]


@pytest.mark.parametrize("event_id", EVENTS)
def test_same_event_gives_different_impacts(event_id: str) -> None:
    """Paso 6 del guion: la misma noticia afecta distinto a Laura y a Javier."""
    laura = Decimal(CASES["expected"][event_id]["laura"]["impact_eur"])
    javier = Decimal(CASES["expected"][event_id]["javier"]["impact_eur"])
    assert laura != javier
