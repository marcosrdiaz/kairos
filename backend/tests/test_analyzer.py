"""`agents/analyzer.py`: salida validada, reintento y fallo. Claude siempre falso."""

from collections.abc import Iterator
from typing import Any

import pytest
from pydantic import ValidationError

from app.agents import analyzer
from app.agents.analyzer import AnalyzerDraft, AnalyzerError
from app.schemas.common import Factor
from app.schemas.events import (
    Channel,
    Direction,
    EventIn,
    EventObserved,
    EventType,
    Relevance,
)
from tests.fakes.claude import FakeClaude


def _event() -> EventIn:
    return EventIn(
        id="nvda-2025-02",
        type=EventType.EARNINGS,
        title="NVIDIA presenta resultados",
        occurred_at="2025-02-26T21:20:00Z",
        text="NVIDIA publica sus resultados del trimestre.",
        source_urls=["https://example.com"],
        observed=EventObserved(
            factors={Factor.EQ_US_TECH: "-0.02"},
            companies={"NVDA": "-0.08"},
        ),
        fallback_chain=["Cadena de respaldo"],
        illustrative=False,
    )


def _draft(**changes: Any) -> AnalyzerDraft:
    values: dict[str, Any] = {
        "event_type": EventType.EARNINGS,
        "entities": [],
        "channels": [
            Channel(
                factor=Factor.EQ_US_TECH,
                direction=Direction.DOWN,
                label="tecnológicas",
                rationale="Caen las tecnológicas",
            )
        ],
        "companies": [],
        "causal_chain": ["NVIDIA decepciona", "Caen las tecnológicas"],
        "relevance": Relevance.HIGH,
    }
    return AnalyzerDraft(**(values | changes))


@pytest.fixture
def use_fake() -> Iterator[Any]:
    def install(*outcomes: Any) -> FakeClaude:
        fake = FakeClaude(*outcomes)
        analyzer.set_client(fake)
        return fake

    yield install
    analyzer.set_client(None)


def test_analysis_keeps_draft_and_adds_identity(use_fake: Any) -> None:
    use_fake(_draft())
    analysis = analyzer.analyze(_event())
    assert analysis.event_id == "nvda-2025-02"
    assert analysis.schema_version == 1
    assert analysis.fallback is False
    assert analysis.analyzed_model == "claude-sonnet-5-5"
    assert analysis.causal_chain == ["NVIDIA decepciona", "Caen las tecnológicas"]


def test_prompt_has_event_and_allowed_keys_but_no_observed_magnitudes(use_fake: Any) -> None:
    fake = use_fake(_draft())
    analyzer.analyze(_event())
    call = fake.messages.calls[0]
    content = call["messages"][0]["content"]
    assert "NVIDIA publica sus resultados" in content
    assert "NVDA" in content
    assert "-0.08" not in content
    assert call["output_format"] is AnalyzerDraft
    assert call["model"] == "claude-sonnet-5-5"


def test_system_prompt_has_no_example_figures(use_fake: Any) -> None:
    fake = use_fake(_draft())
    analyzer.analyze(_event())
    assert not any(ch.isdigit() for ch in fake.messages.calls[0]["system"])


def test_retries_once_with_the_failure_as_feedback(use_fake: Any) -> None:
    fake = use_fake(RuntimeError("fallo de red"), _draft())
    assert analyzer.analyze(_event()).fallback is False
    assert len(fake.messages.calls) == 2
    assert "intento anterior" in fake.messages.calls[1]["messages"][0]["content"]


def test_fails_after_second_error(use_fake: Any) -> None:
    fake = use_fake(RuntimeError("uno"), RuntimeError("dos"))
    with pytest.raises(AnalyzerError):
        analyzer.analyze(_event())
    assert len(fake.messages.calls) == 2


def test_refusal_counts_as_failure(use_fake: Any) -> None:
    use_fake(None, None)
    with pytest.raises(AnalyzerError):
        analyzer.analyze(_event())


@pytest.mark.parametrize(
    "text",
    [
        "Compra más acciones",
        "Vende tus fondos",
        "Te recomiendo esperar",
        "Deberías invertir en bonos",
        "Es buen momento para entrar",
        "Invierte en oro",
        "Sal de la bolsa",
    ],
)
def test_order_in_chain_is_rejected(use_fake: Any, text: str) -> None:
    fake = use_fake(_draft(causal_chain=[text]), _draft(causal_chain=[text]))
    with pytest.raises(AnalyzerError):
        analyzer.analyze(_event())
    assert len(fake.messages.calls) == 2


def test_order_in_rationale_is_rejected(use_fake: Any) -> None:
    channel = Channel(
        factor=Factor.EQ_US_TECH,
        direction=Direction.UP,
        label="tecnológicas",
        rationale="Conviene comprar ahora, compra",
    )
    use_fake(_draft(channels=[channel]), _draft(channels=[channel]))
    with pytest.raises(AnalyzerError):
        analyzer.analyze(_event())


def test_digits_are_rejected_by_the_draft_schema() -> None:
    with pytest.raises(ValidationError):
        _draft(causal_chain=["Sube un cinco por 100"])


def test_without_api_key_fails_without_calling() -> None:
    with pytest.raises(AnalyzerError):
        analyzer.analyze(_event())
