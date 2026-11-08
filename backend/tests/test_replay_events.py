"""Eventos de replay de T0-10 (`data/events/replay/*.json`).

Comprueba que cada JSON valida contra `EventIn` y que cumple las reglas de la tarea: aún sin
`observed`, eventos reales, `fallback_chain` sin cifras ni órdenes y consenso solo en el BCE.
"""

import re
from pathlib import Path

import pytest

from app.schemas.common import Factor
from app.schemas.events import EventIn

REPLAY_DIR = Path(__file__).resolve().parents[2] / "data" / "events" / "replay"
EXPECTED_IDS = {"bce-2025-06", "oil-2025-06", "nvda-2025-02"}
DIGIT = re.compile(r"\d")
ORDER_WORDS = re.compile(r"compra|vende|recomiend|deberías", re.IGNORECASE)


def _files() -> list[Path]:
    return sorted(REPLAY_DIR.glob("*.json"))


def _load(path: Path) -> EventIn:
    return EventIn.model_validate_json(path.read_text(encoding="utf-8"))


def test_expected_events_exist() -> None:
    assert {p.stem for p in _files()} == EXPECTED_IDS


@pytest.mark.parametrize("path", _files(), ids=lambda p: p.stem)
def test_event_is_valid(path: Path) -> None:
    event = _load(path)
    assert event.id == path.stem
    assert event.observed is not None
    assert set(event.observed.factors) == set(Factor)
    assert event.observed_source
    assert event.illustrative is False
    assert event.source_urls
    assert all(url.startswith("https://") for url in event.source_urls)


@pytest.mark.parametrize("path", _files(), ids=lambda p: p.stem)
def test_fallback_chain_has_no_digits_or_orders(path: Path) -> None:
    event = _load(path)
    assert event.fallback_chain
    for step in event.fallback_chain:
        assert not DIGIT.search(step), step
        assert not ORDER_WORDS.search(step), step


@pytest.mark.parametrize("path", _files(), ids=lambda p: p.stem)
def test_text_has_no_orders(path: Path) -> None:
    assert not ORDER_WORDS.search(_load(path).text)


def test_only_ecb_has_consensus() -> None:
    with_consensus = {p.stem for p in _files() if _load(p).consensus is not None}
    assert with_consensus == {"bce-2025-06"}
