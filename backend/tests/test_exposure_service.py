"""`exposure/service.py`: look-through real de las carteras del seed, composición y API."""

from decimal import Decimal

from fastapi.testclient import TestClient

from app.core import trace
from app.exposure import service
from app.main import API_PREFIX
from app.schemas.common import SourceKind

_TOLERANCE = Decimal("0.002")
LAURA = f"{API_PREFIX}/portfolios/laura"


def _weight(buckets: list[dict[str, str]], key: str) -> Decimal:
    return next(Decimal(b["weight"]) for b in buckets if b["key"] == key)


def test_laura_matches_figures_of_the_compositions_decision(client: TestClient) -> None:
    body = client.get(f"{LAURA}/exposure").json()
    assert abs(_weight(body["by_country"], "US") - Decimal("0.637")) <= _TOLERANCE
    radiography = body["radiography"]
    assert radiography["num_holdings"] == 3
    assert radiography["top_country"]["key"] == "US"
    assert radiography["top_companies_group"]["n"] == 7
    assert (
        abs(Decimal(radiography["top_companies_group"]["weight"]) - Decimal("0.259")) <= _TOLERANCE
    )
    assert abs(Decimal(body["coverage_pct"]) - Decimal("0.943")) <= _TOLERANCE


def test_buckets_cover_the_whole_portfolio(client: TestClient) -> None:
    body = client.get(f"{LAURA}/exposure").json()
    total = Decimal(client.get(LAURA).json()["total_eur"])
    for field in ("by_country", "by_sector", "by_currency"):
        assert abs(sum(Decimal(b["value_eur"]) for b in body[field]) - total) <= Decimal("0.50")


def test_direct_stock_overlaps_with_funds(client: TestClient) -> None:
    body = client.get(f"{LAURA}/exposure").json()
    nvda = next(o for o in body["overlap"] if o["key"] == "NVDA")
    assert "US67066G1040" in nvda["asset_ids"]
    assert "IE00B4L5Y983" in nvda["asset_ids"]
    company = next(c for c in body["top_companies"] if c["key"] == "NVDA")
    direct = next(h for h in company["held_in"] if h["asset_id"] == "US67066G1040")
    assert direct["weight_in_asset"] == "1"


def test_direct_stock_takes_country_and_sector_from_compositions(client: TestClient) -> None:
    body = client.get(f"{LAURA}/exposure").json()
    assert _weight(body["by_country"], "ES") > Decimal("0.05")


def test_no_residual_keys_in_companies(client: TestClient) -> None:
    body = client.get(f"{LAURA}/exposure").json()
    for company in [*body["top_companies"], *body["overlap"]]:
        assert not company["key"].startswith(("OTROS_", "GOV_", "BONOS_"))


def test_deposit_and_pension_plan_lower_coverage(client: TestClient) -> None:
    body = client.get(f"{API_PREFIX}/portfolios/javier/exposure").json()
    assert Decimal(body["coverage_pct"]) < Decimal("0.80")
    assert body["radiography"]["num_holdings"] == 3
    assert _weight(body["by_currency"], "EUR") > Decimal("0.5")


def test_exposure_is_traced_with_composition_sources(client: TestClient) -> None:
    exposure = service.get_exposure("laura")
    record = trace.get(exposure.calc_id)
    assert record is not None
    assert record.kind == "exposure"
    assert len(record.parent_calc_ids) == 1
    assert {s["kind"] for s in record.sources} == {SourceKind.COMPOSITION.value}
    assert exposure.as_of.date().isoformat() == "2026-09-30"


def test_unknown_portfolio_is_404(client: TestClient) -> None:
    assert client.get(f"{API_PREFIX}/portfolios/nadie/exposure").status_code == 404


def test_company_weights_reads_named_rows_only(client: TestClient) -> None:
    weights = service.company_weights(["IE00B4L5Y983", "IE0007472115"], {"NVDA", "NADA"})
    assert weights == {"IE00B4L5Y983": {"NVDA": Decimal("0.04748547")}}


def test_company_weights_without_companies_is_empty(client: TestClient) -> None:
    assert service.company_weights(["IE00B4L5Y983"], ()) == {}


def test_load_compositions_is_idempotent(client: TestClient) -> None:
    first = service.load_compositions()
    assert service.load_compositions() == first
    assert first > 0
