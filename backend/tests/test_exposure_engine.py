"""`exposure/engine.py`: look-through (`SPEC.md` §8.4) con casos calculados a mano."""

from decimal import Decimal as D

from app.exposure.engine import Constituent, HoldingIn, compute_exposure
from app.schemas.common import AssetType


def part(
    key: str,
    weight: str,
    country: str | None = "US",
    sector: str | None = "information_technology",
    currency: str | None = "USD",
) -> Constituent:
    return Constituent(key, key.title(), D(weight), country, sector, currency)


def holding(
    asset_id: str,
    value: str,
    *parts: Constituent,
    asset_type: AssetType = AssetType.ETF,
) -> HoldingIn:
    return HoldingIn(asset_id, asset_id, asset_type, D(value), parts)


def test_buckets_add_value_times_weight() -> None:
    result = compute_exposure(
        [
            holding("F", "1000", part("A", "0.6"), part("B", "0.4", country="JP", currency="JPY")),
            holding("S", "1000", part("A", "1"), asset_type=AssetType.STOCK),
        ]
    )
    assert [(b.key, b.value_eur, b.weight) for b in result.by_country] == [
        ("US", D("1600"), D("0.8000")),
        ("JP", D("400"), D("0.2000")),
    ]
    assert result.by_country[0].label == "Estados Unidos"
    assert [b.key for b in result.by_currency] == ["USD", "JPY"]
    assert result.by_currency[0].label == "Dólar"
    assert result.by_sector[0].label == "Tecnología"


def test_unknown_values_go_to_other_and_last() -> None:
    result = compute_exposure(
        [
            holding(
                "F",
                "1000",
                part("A", "0.9", country=None, sector=None, currency=""),
                part("B", "0.1", country="ES", sector="energy", currency="EUR"),
            )
        ]
    )
    assert [b.key for b in result.by_country] == ["ES", "OTHER"]
    assert [b.key for b in result.by_sector] == ["energy", "other"]
    assert [b.key for b in result.by_currency] == ["EUR", "OTHER"]
    assert result.by_country[1].label == "Otros"


def test_unlabelled_key_is_shown_as_is() -> None:
    result = compute_exposure([holding("F", "100", part("A", "1", country="XX"))])
    assert result.by_country[0].label == "XX"


def test_coverage_is_share_with_known_country() -> None:
    result = compute_exposure(
        [holding("F", "1000", part("A", "0.75"), part("OTROS_OTHER", "0.25", country="OTHER"))]
    )
    assert result.coverage_pct == D("0.7500")


def test_sector_does_not_count_for_coverage() -> None:
    result = compute_exposure([holding("F", "1000", part("A", "1", sector="other"))])
    assert result.coverage_pct == D("1.0000")


def test_companies_combine_funds_and_direct_stock() -> None:
    result = compute_exposure(
        [
            holding("F", "1000", part("AAPL", "0.05"), part("OTROS_US", "0.95")),
            holding("S", "100", part("AAPL", "1"), asset_type=AssetType.STOCK),
        ]
    )
    company = result.top_companies[0]
    assert (company.key, company.value_eur, company.weight) == ("AAPL", D("150"), D("0.1364"))
    assert [(h.asset_id, h.weight_in_asset) for h in company.held_in] == [
        ("S", D("1")),
        ("F", D("0.05")),
    ]


def test_direct_stock_name_wins_over_composition_name() -> None:
    fund = Constituent("AAPL", "APPLE INC", D("0.5"), "US", "x", "USD")
    stock = Constituent("AAPL", "Apple Inc.", D("1"), "US", "x", "USD")
    result = compute_exposure(
        [
            holding("F", "1000", fund),
            HoldingIn("S", "S", AssetType.STOCK, D("10"), (stock,)),
        ]
    )
    assert result.top_companies[0].name == "Apple Inc."


def test_non_company_keys_stay_out_of_companies_but_count_in_buckets() -> None:
    result = compute_exposure(
        [
            holding("F", "100", part("OTROS_US", "0.5"), part("GOV_FR", "0.3", country="FR")),
            holding("G", "100", part("BONOS_US", "0.2"), part("OTROS_US", "0.8")),
        ]
    )
    assert result.top_companies == []
    assert result.overlap == []
    assert sum(b.value_eur for b in result.by_country) == D("180")


def test_overlap_needs_two_positions() -> None:
    result = compute_exposure(
        [
            holding("F", "1000", part("AAPL", "0.1"), part("SOLO", "0.2")),
            holding("G", "1000", part("AAPL", "0.2")),
        ]
    )
    assert [(o.key, o.weight, o.asset_ids) for o in result.overlap] == [
        ("AAPL", D("0.1500"), ["F", "G"])
    ]


def test_top_companies_are_limited_and_sorted() -> None:
    parts = [part(f"C{i:02d}", "0.04") for i in range(25)]
    result = compute_exposure([holding("F", "1000", *parts)])
    assert len(result.top_companies) == 20
    assert result.top_companies[0].key == "C00"


def test_radiography_counts_funds_and_top_seven() -> None:
    parts = [part(f"C{i}", weight) for i, weight in enumerate(("0.3", *["0.1"] * 6))]
    result = compute_exposure(
        [
            holding("F", "900", *parts, part("C7", "0.05"), part("OTROS_US", "0.05")),
            holding("S", "100", part("C8", "1"), asset_type=AssetType.STOCK),
            holding("D", "0", part("OTROS_D", "1", country="OTHER"), asset_type=AssetType.DEPOSIT),
        ]
    )
    radiography = result.radiography
    assert radiography.num_holdings == 1
    assert radiography.top_country.key == "US"
    assert radiography.top_country.weight == D("1.0000")
    assert radiography.top_companies_group.n == 7
    # 0,9 · (0,3 + 5 · 0,1) + 0,1 = 0,82: entra la acción directa y sale una de 0,09.
    assert radiography.top_companies_group.weight == D("0.8200")


def test_top_country_ignores_other() -> None:
    result = compute_exposure(
        [holding("F", "100", part("A", "0.9", country="OTHER"), part("B", "0.1", country="ES"))]
    )
    assert result.radiography.top_country.key == "ES"


def test_only_unknown_countries() -> None:
    result = compute_exposure([holding("F", "100", part("A", "1", country="OTHER"))])
    top = result.radiography.top_country
    assert (top.key, top.label, top.weight) == ("OTHER", "Otros", D("0.0000"))


def test_empty_portfolio() -> None:
    result = compute_exposure([])
    assert result.by_country == []
    assert result.coverage_pct == D("0.0000")
    assert result.radiography.num_holdings == 0
    assert result.radiography.top_companies_group.weight == D("0.0000")
