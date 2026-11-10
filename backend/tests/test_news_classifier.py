"""Clasificador de noticias (T4-29) con FakeClaude: validación por noticia, regla 1 y guardado."""

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import pytest

from app.agents import news_classifier
from app.agents.news_classifier import BatchDraft, ChannelDraft, ItemDraft, NewsInput
from app.news import repository, service
from app.news.ingest.sources import RawNews
from app.schemas.events import Relevance
from tests.fakes.claude import FakeClaude

NOV_9 = datetime(2026, 11, 9, 10, tzinfo=UTC)
COMPANIES = {"NVDA": "NVIDIA", "MSFT": "Microsoft"}


@pytest.fixture(autouse=True)
def _no_real_client() -> Iterator[None]:
    yield
    news_classifier.set_client(None)


def _item(index: int = 0, **changes: Any) -> ItemDraft:
    data: dict[str, Any] = {
        "index": index,
        "category": "company",
        "relevance": "high",
        "companies": ["NVDA"],
        "channels": [
            ChannelDraft(
                company_key="NVDA",
                direction="down",
                label="NVIDIA",
                rationale="La investigación pesa sobre la acción.",
            ),
            ChannelDraft(
                factor="EQ_US_TECH",
                direction="down",
                label="tecnológicas",
                rationale="NVIDIA pesa mucho en los índices tecnológicos.",
            ),
        ],
        "causal_chain": ["NVIDIA investiga a su consejero delegado.", "La acción cae."],
        "summary_es": "NVIDIA abre una investigación sobre su consejero delegado.",
    }
    data.update(changes)
    return ItemDraft(**data)


def _input(index: int = 0) -> NewsInput:
    return NewsInput(index, "Nvidia investiga a su CEO", "", "El Mundo", NOV_9)


def test_valid_classification_is_accepted() -> None:
    news_classifier.set_client(FakeClaude(BatchDraft(items=[_item()])))
    [result] = news_classifier.classify([_input()], COMPANIES).values()
    assert result.relevance is Relevance.HIGH
    assert [c.name for c in result.companies] == ["NVIDIA"]
    assert [(c.company_key, c.factor) for c in result.channels] == [
        ("NVDA", None),
        (None, "EQ_US_TECH"),
    ]


@pytest.mark.parametrize(
    "changes",
    [
        {"summary_es": "NVIDIA cae un 5 %."},  # regla 1: sin cifras
        {"causal_chain": ["La acción cae.", "Es buen momento para comprar."]},  # sin consejos
        {"category": "sports"},
        {"relevance": "enorme"},
    ],
)
def test_invalid_items_are_left_unclassified(changes: dict[str, Any]) -> None:
    news_classifier.set_client(FakeClaude(BatchDraft(items=[_item(**changes), _item(1)])))
    accepted = news_classifier.classify([_input(0), _input(1)], COMPANIES)
    assert list(accepted) == [1]


def test_unknown_companies_and_their_channels_are_dropped() -> None:
    draft = _item(
        companies=["NVDA", "AMD"],
        channels=[ChannelDraft(company_key="AMD", direction="up", label="AMD", rationale="Sube.")],
    )
    news_classifier.set_client(FakeClaude(BatchDraft(items=[draft])))
    [result] = news_classifier.classify([_input()], COMPANIES).values()
    assert [c.key for c in result.companies] == ["NVDA"] and result.channels == []


def test_low_relevance_has_no_channels() -> None:
    news_classifier.set_client(FakeClaude(BatchDraft(items=[_item(relevance="low")])))
    [result] = news_classifier.classify([_input()], COMPANIES).values()
    assert result.channels == []


def test_refusal_is_an_error() -> None:
    news_classifier.set_client(FakeClaude(None))
    with pytest.raises(news_classifier.ClassifierError):
        news_classifier.classify([_input()], COMPANIES)


def test_the_prompt_has_no_example_figures() -> None:
    """CLAUDE.md: nada de cifras de ejemplo en los prompts (el modelo las copia)."""
    assert not any(ch.isdigit() for ch in news_classifier._prompt())


def test_classify_pending_saves_and_does_not_repeat(db: None) -> None:
    raws = [
        RawNews(f"https://elmundo.es/{i}", f"Titular {i}", "", NOV_9, "El Mundo", "x", "es", "q")
        for i in range(2)
    ]
    repository.save_new(raws, NOV_9)
    fake = FakeClaude(BatchDraft(items=[_item(0), _item(1, summary_es="Con 3 cifras.")]))
    news_classifier.set_client(fake)
    assert service.classify_pending() == 1
    classified = [r for r in repository.list_items() if r.classification]
    assert len(classified) == 1
    assert classified[0].classifier_key == news_classifier.classifier_key()
    # La que falló se vuelve a intentar; la ya clasificada, no.
    fake.messages.outcomes.append(BatchDraft(items=[_item(0)]))
    assert service.classify_pending() == 1
    assert len(fake.messages.calls[-1]["messages"][0]["content"].split("[0]")) == 2
