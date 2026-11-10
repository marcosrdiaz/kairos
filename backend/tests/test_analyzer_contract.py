"""Contrato de `EventAnalysis.prompt_version` (T2-26, D-083): campo opcional y aditivo."""

from app.schemas import examples
from app.schemas.events import EventAnalysis


def _base() -> dict[str, object]:
    data = examples.load("EventAnalysis")
    assert isinstance(data, dict)
    return data


def test_example_carries_the_prompt_version() -> None:
    assert EventAnalysis.model_validate(_base()).prompt_version == "3f9a2c1e7b04"


def test_analyses_saved_before_the_field_still_validate() -> None:
    data = _base()
    data.pop("prompt_version")
    assert EventAnalysis.model_validate(data).prompt_version is None
