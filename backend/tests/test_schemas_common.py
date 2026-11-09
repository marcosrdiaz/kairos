from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.common import (
    ContractModel,
    Fraction,
    Money,
    Price,
    SourceKind,
    SourceRef,
    Units,
    UtcDatetime,
)


class _Sample(ContractModel):
    amount: Money
    units: Units
    price: Price
    weight: Fraction
    at: UtcDatetime


def _sample(**overrides: object) -> _Sample:
    data: dict[str, object] = {
        "amount": "40123.455",
        "units": "152.304512",
        "price": "95.42",
        "weight": "0.76",
        "at": "2026-11-08T19:00:00+01:00",
    }
    data.update(overrides)
    return _Sample.model_validate(data)


def test_serializes_decimals_as_strings_with_contract_precision() -> None:
    dumped = _sample().model_dump(mode="json")
    assert dumped["amount"] == "40123.46"  # ROUND_HALF_EVEN: ...455 → ...46 (5 tras 5 impar)
    assert dumped["units"] == "152.30451200"
    assert dumped["price"] == "95.42000000"
    assert dumped["weight"] == "0.76"
    assert dumped["at"] == "2026-11-08T18:00:00Z"


def test_money_rounds_half_even() -> None:
    assert _sample(amount="0.125").model_dump(mode="json")["amount"] == "0.12"
    assert _sample(amount="-0.135").model_dump(mode="json")["amount"] == "-0.14"


def test_fraction_never_uses_exponent() -> None:
    assert _sample(weight=Decimal("1E-7")).model_dump(mode="json")["weight"] == "0.0000001"


def test_zero_keeps_fixed_point_with_contract_precision() -> None:
    """`Decimal(0).quantize(...)` es `0E-8`: el contrato exige `0.00000000` (venta total, T1-04)."""
    dumped = _sample(amount=Decimal(0), units=Decimal(0), price=Decimal("0E-12")).model_dump(
        mode="json"
    )
    assert (dumped["amount"], dumped["units"], dumped["price"]) == (
        "0.00",
        "0.00000000",
        "0.00000000",
    )


def test_values_stay_decimal_in_python() -> None:
    sample = _sample()
    assert isinstance(sample.amount, Decimal)
    assert sample.at.tzinfo == UTC


def test_naive_datetime_rejected() -> None:
    with pytest.raises(ValidationError):
        _sample(at="2026-11-08T18:00:00")


def test_extra_fields_rejected() -> None:
    with pytest.raises(ValidationError):
        _sample(illustrative=True)


def test_source_ref_example_from_design() -> None:
    ref = SourceRef.model_validate(
        {
            "kind": "price",
            "label": "VL iShares Core MSCI World",
            "ref": "IE00B4L5Y983",
            "as_of": "2026-11-06T00:00:00Z",
            "url": None,
        }
    )
    assert ref.kind is SourceKind.PRICE
    assert ref.as_of == datetime(2026, 11, 6, tzinfo=UTC)
    assert ref.model_dump(mode="json")["as_of"] == "2026-11-06T00:00:00Z"


def test_utc_conversion_from_other_offset() -> None:
    ref = SourceRef(
        kind=SourceKind.FX,
        label="EURUSD",
        ref="EURUSD",
        as_of=datetime(2026, 11, 6, 2, 0, tzinfo=timezone(timedelta(hours=2))),
    )
    assert ref.model_dump(mode="json")["as_of"] == "2026-11-06T00:00:00Z"
