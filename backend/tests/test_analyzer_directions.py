"""Dirección observada en el analizador (T2-26, D-083). Claude siempre falso."""

import re
from collections.abc import Iterator
from decimal import Decimal
from typing import Any

import pytest

from app.agents import analyzer, analyzer_directions
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

BCE_OBSERVED = {
    Factor.RATES_EUR: Decimal("0.00024"),  # la rentabilidad subió aunque el BCE bajara tipos
    Factor.EURUSD: Decimal("0.0033"),  # el euro subió
    Factor.EQ_GLOBAL: Decimal("0.00085"),
    Factor.EQ_US_TECH: Decimal("-0.00803"),
    Factor.OIL: Decimal("0.0074"),
}


def _event() -> EventIn:
    return EventIn(
        id="bce-2025-06",
        type=EventType.CENTRAL_BANK,
        title="El BCE baja los tipos",
        occurred_at="2025-06-05T12:15:00Z",
        text="El BCE recorta los tipos oficiales.",
        source_urls=["https://example.com"],
        observed=EventObserved(factors=BCE_OBSERVED, companies={}),
        fallback_chain=["Cadena de respaldo"],
        illustrative=False,
    )


def _channel(factor: Factor, direction: Direction) -> Channel:
    return Channel(factor=factor, direction=direction, label="etiqueta", rationale="Motivo")


def _draft(chain: list[str], channels: list[Channel] | None = None) -> AnalyzerDraft:
    return AnalyzerDraft(
        event_type=EventType.CENTRAL_BANK,
        entities=[],
        channels=channels or [_channel(Factor.RATES_EUR, Direction.DOWN)],
        companies=[],
        causal_chain=chain,
        relevance=Relevance.HIGH,
    )


@pytest.fixture
def use_fake() -> Iterator[Any]:
    def install(*outcomes: Any) -> FakeClaude:
        fake = FakeClaude(*outcomes)
        analyzer.set_client(fake)
        return fake

    yield install
    analyzer.set_client(None)


# --- Funciones puras ---


def test_describe_gives_direction_without_magnitude() -> None:
    text = analyzer_directions.describe(BCE_OBSERVED)
    assert "RATES_EUR: sube" in text
    assert "EQ_US_TECH: baja" in text
    assert not re.search(r"\d", text)


def test_correct_sets_the_observed_direction() -> None:
    channels = [_channel(Factor.RATES_EUR, Direction.DOWN), _channel(Factor.EURUSD, Direction.DOWN)]
    fixed = analyzer_directions.correct(channels, BCE_OBSERVED)
    assert [c.direction for c in fixed] == [Direction.UP, Direction.UP]


@pytest.mark.parametrize(
    "sentence",
    [
        "La rentabilidad de los bonos en euros baja.",
        "El euro se debilita frente al dólar.",
        "El dólar sube frente al euro.",
        "El petróleo cae con fuerza.",
        "Las tecnológicas suben.",
    ],
)
def test_check_chain_rejects_a_contradiction(sentence: str) -> None:
    with pytest.raises(ValueError, match="pero ese día"):
        analyzer_directions.check_chain([sentence], BCE_OBSERVED)


@pytest.mark.parametrize(
    "sentence",
    [
        "El BCE baja los tipos oficiales.",  # el tipo oficial no es la rentabilidad del bono
        "Pese a la bajada del BCE, la rentabilidad de los bonos sube ligeramente.",
        "El euro se fortalece.",
        "El dólar se debilita.",
        "Las tecnológicas caen y el petróleo sube.",  # dos factores: no se juzga
        "Los mercados reaccionan con calma.",
    ],
)
def test_check_chain_accepts_coherent_or_ambiguous_sentences(sentence: str) -> None:
    analyzer_directions.check_chain([sentence], BCE_OBSERVED)


# --- En el analizador ---


def test_prompt_carries_directions_but_no_magnitudes(use_fake: Any) -> None:
    fake = use_fake(_draft(["El BCE baja los tipos oficiales."]))
    analyzer.analyze(_event())
    content = fake.messages.calls[0]["messages"][0]["content"]
    assert "RATES_EUR: sube" in content
    assert "EURUSD: sube" in content
    assert "0.00024" not in content and "0.0033" not in content


def test_model_direction_is_corrected_to_the_observed_one(use_fake: Any) -> None:
    use_fake(_draft(["El BCE baja los tipos oficiales."]))
    analysis = analyzer.analyze(_event())
    [channel] = analysis.channels
    assert channel.factor is Factor.RATES_EUR
    assert channel.direction is Direction.UP


def test_contradicting_chain_is_retried_with_the_reason(use_fake: Any) -> None:
    bad = _draft(["El BCE baja los tipos.", "La rentabilidad de los bonos baja."])
    good = _draft(["El BCE baja los tipos.", "Aun así, la rentabilidad de los bonos sube."])
    fake = use_fake(bad, good)

    analysis = analyzer.analyze(_event())

    assert analysis.causal_chain == good.causal_chain
    feedback = fake.messages.calls[1]["messages"][0]["content"]
    assert "RATES_EUR baja, pero ese día sube" in feedback


def test_two_contradicting_chains_fall_back(use_fake: Any) -> None:
    bad = _draft(["El euro pierde valor frente al dólar."])
    use_fake(bad, bad)
    with pytest.raises(AnalyzerError):
        analyzer.analyze(_event())


def test_analysis_records_the_prompt_version(use_fake: Any) -> None:
    use_fake(_draft(["El BCE baja los tipos oficiales."]))
    version = analyzer.analyze(_event()).prompt_version
    assert version is not None
    assert re.fullmatch(r"[0-9a-f]{12}", version)
    assert version == analyzer.prompt_version()


def test_input_key_changes_with_the_prompt_or_the_event() -> None:
    event = _event()
    key = analyzer.input_key(event)
    assert key.startswith(analyzer.prompt_version())
    flipped = {**BCE_OBSERVED, Factor.OIL: Decimal("-0.01")}
    other = event.model_copy(update={"observed": EventObserved(factors=flipped, companies={})})
    assert analyzer.input_key(other) != key
    assert analyzer.input_key(event) == key


def test_timeout_is_ten_seconds() -> None:
    assert analyzer._TIMEOUT_S == 10.0
