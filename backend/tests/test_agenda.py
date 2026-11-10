"""Agenda de próximos eventos (T2-06, diseño del MVP §4.3, D-080).

Las funciones puras se comprueban con cifras a mano. El servicio usa el seed de Laura, los precios
reales de `data/prices`, el reloj de demo (2026-11-06 18:00 UTC) y betas sintéticas: así se sabe
qué posiciones deben entrar en cada evento.
"""

from collections.abc import Iterator
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core import clock, trace
from app.exposure import service as exposure_service
from app.impact import repository as impact_repository
from app.impact.betas import BetaEstimate
from app.main import API_PREFIX
from app.planning import agenda, service
from app.portfolio import service as portfolio_service
from app.schemas.common import Factor
from app.schemas.planning import AgendaItemOut

D = Decimal
DEMO_NOW = datetime(2026, 11, 6, 18, 0, tzinfo=UTC)

NVDA_STOCK = "US67066G1040"
BOND_FUND = "IE00B18GC888"
WORLD_FUND = "IE00B4L5Y983"
NO_BETAS = {"DEP-12M", "PP-MIXTO"}


# --- Funciones puras ---


def test_event_date_adds_offset_days_at_the_given_utc_time() -> None:
    assert agenda.event_date(DEMO_NOW, 6, "13:15") == datetime(2026, 11, 12, 13, 15, tzinfo=UTC)


def test_event_date_uses_the_day_of_now_not_its_time() -> None:
    late = datetime(2026, 11, 6, 23, 59, tzinfo=UTC)
    assert agenda.event_date(late, 0, "08:00") == datetime(2026, 11, 6, 8, 0, tzinfo=UTC)


def test_factor_exposure_sums_positions_with_abs_beta_at_least_threshold() -> None:
    values = {"a": D("100"), "b": D("200"), "c": D("50"), "d": D("70")}
    betas = {
        "a": {Factor.OIL: D("0.05")},  # por debajo del umbral
        "b": {Factor.OIL: D("-0.30")},  # negativa: cuenta por valor absoluto
        "c": {Factor.EQ_GLOBAL: D("1")},  # otro factor
        "d": {Factor.OIL: D("0.1")},  # justo en el umbral
    }
    assert agenda.factor_exposure(values, betas, Factor.OIL) == D("270")


def test_factor_exposure_is_zero_without_betas() -> None:
    assert agenda.factor_exposure({"a": D("100")}, {}, Factor.OIL) == D("0")


def test_company_exposure_is_value_times_look_through_weight() -> None:
    values = {"fund": D("1000"), "stock": D("500"), "other": D("300")}
    weights = {"fund": {"NVDA": D("0.05")}, "stock": {"NVDA": D("1")}}
    assert agenda.company_exposure(values, weights, "NVDA") == D("550")


def test_exposed_weight_is_share_of_total_and_zero_for_empty_portfolio() -> None:
    assert agenda.exposed_weight(D("550"), D("1100")) == D("0.5000")
    assert agenda.exposed_weight(D("1"), D("3")) == D("0.3333")
    assert agenda.exposed_weight(D("0"), D("0")) == D("0")


def test_load_events_reads_the_demo_agenda() -> None:
    events = agenda.load_events()
    assert [e.id for e in events] == [
        "macro-us-cpi",
        "ecb-meeting",
        "opec-meeting",
        "nvda-earnings",
    ]
    nvda = events[-1]
    assert nvda.factor is Factor.EQ_US_TECH and nvda.company == "NVDA"
    assert events[1].company is None


# --- Servicio con el seed de Laura ---


@pytest.fixture
def laura(client: TestClient) -> Iterator[None]:
    """Reloj de demo y betas sintéticas: β 1 a `EQ_GLOBAL` en todo lo que cotiza;
    `RATES_EUR` −2 en el fondo de bonos y 0,05 (por debajo del umbral) en el MSCI World."""
    clock.set_now(DEMO_NOW)
    ids = {p.asset_id for p in portfolio_service.get_valued("laura").positions} - NO_BETAS

    def beta(asset_id: str, factor: Factor, value: str) -> BetaEstimate:
        return BetaEstimate(
            asset_id=asset_id,
            factor=factor,
            beta=D(value),
            std_err=D("0.01"),
            r2=D("0.8"),
            n_obs=700,
            window_start=date(2023, 11, 7),
            window_end=date(2026, 11, 6),
        )

    impact_repository.replace_betas(
        [beta(a, Factor.EQ_GLOBAL, "1") for a in ids]
        + [beta(BOND_FUND, Factor.RATES_EUR, "-2"), beta(WORLD_FUND, Factor.RATES_EUR, "0.05")]
    )
    yield
    clock.reset()


def _values() -> dict[str, Decimal]:
    return {p.asset_id: p.value_eur for p in portfolio_service.get_valued("laura").positions}


def _by_kind(items: list[AgendaItemOut]) -> dict[str, AgendaItemOut]:
    return {item.kind: item for item in items}


def test_agenda_is_sorted_and_dated_from_the_demo_clock(laura: None) -> None:
    items = service.get_agenda("laura")
    assert [(i.kind, i.date) for i in items] == [
        ("macro", datetime(2026, 11, 10, 13, 30, tzinfo=UTC)),
        ("central_bank", datetime(2026, 11, 12, 13, 15, tzinfo=UTC)),
        ("commodity", datetime(2026, 11, 18, 12, 0, tzinfo=UTC)),
        ("earnings", datetime(2026, 11, 19, 21, 20, tzinfo=UTC)),
        ("dca", datetime(2026, 12, 5, 0, 0, tzinfo=UTC)),
    ]


def test_factor_events_count_only_positions_over_the_beta_threshold(laura: None) -> None:
    values = _values()
    total = sum(values.values(), D("0"))
    items = _by_kind(service.get_agenda("laura"))

    ecb = items["central_bank"]
    assert ecb.factor is Factor.RATES_EUR
    assert ecb.exposed_eur == values[BOND_FUND]
    assert ecb.exposed_weight == agenda.exposed_weight(values[BOND_FUND], total)

    cpi = items["macro"]
    priced = sum((v for a, v in values.items() if a not in NO_BETAS), D("0"))
    assert cpi.exposed_eur == priced

    opec = items["commodity"]  # sin betas al petróleo: la cita sale, con exposición cero
    assert opec.exposed_eur == D("0") and opec.exposed_weight == D("0")


def test_earnings_use_look_through_plus_the_direct_stock(laura: None) -> None:
    values = _values()
    weights = exposure_service.company_weights(list(values), ["NVDA"])
    expected = values[NVDA_STOCK] + sum((values[a] * w["NVDA"] for a, w in weights.items()), D("0"))
    nvda = _by_kind(service.get_agenda("laura"))["earnings"]
    assert weights, "la composición de algún fondo de Laura debe incluir NVDA"
    assert nvda.factor is Factor.EQ_US_TECH
    assert nvda.exposed_eur == expected
    assert nvda.title == "Resultados de NVIDIA"


def test_active_dca_is_an_item_without_factor(laura: None) -> None:
    dca = _by_kind(service.get_agenda("laura"))["dca"]
    assert dca.title == "Tu aportación mensual"
    assert dca.exposed_eur == D("300.00")
    assert dca.factor is None and dca.exposed_weight is None


def test_every_item_has_an_agenda_trace(laura: None) -> None:
    for item in service.get_agenda("laura"):
        stored = trace.get(item.calc_id)
        assert stored is not None and stored.kind == "agenda"
        assert stored.parent_calc_ids, "la traza cuelga de la valoración de la cartera"


def test_api_serves_the_real_agenda_not_the_fixed_example(client: TestClient, laura: None) -> None:
    body = client.get(f"{API_PREFIX}/portfolios/laura/agenda").json()
    assert len(body) == 5
    assert "9776.84" not in {item["exposed_eur"] for item in body}  # cifra del ejemplo fijo
    assert client.get(f"{API_PREFIX}/portfolios/nadie/agenda").status_code == 404
