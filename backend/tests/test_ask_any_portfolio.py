"""El asistente sobre cualquier cartera (T4-14), de punta a punta con la BD de prueba.

Tres carteras importadas («Personal», «Negocio» e «Hijos») además de las del seed. Las cifras
del texto guionizado salen siempre del contexto que construye la propia app (`display`), nunca
del test, salvo la suma de carteras, que el test calcula a propósito para ver que se bloquea.
"""

import json
from collections.abc import Iterator
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from app.agents import claude, context, tools
from app.agents.fact_format import format_eur
from app.main import API_PREFIX
from app.portfolio import service as portfolio_service
from app.schemas.agents import AskEvent
from app.voice import service as voice_service
from tests.fakes.claude_stream import FakeStreamingClaude, Reply

_ADAPTER: TypeAdapter[Any] = TypeAdapter(AskEvent)
_CSV = {
    "Personal": ("personal", "asset,units,avg_cost_eur\nIE00BK5BQT80,25,98.40\n"),
    "Negocio": ("business", "asset,units,avg_cost_eur\nNVDA,40,100\n"),
    "Hijos": ("family", "asset,units,avg_cost_eur\nIE00B18GC888,40.5,91.10\n"),
}


@pytest.fixture(autouse=True)
def _clean() -> Iterator[None]:
    context.invalidate()
    voice_service.reset()
    yield
    claude.set_client(None)
    context.invalidate()
    voice_service.reset()


@pytest.fixture
def ids(client: TestClient) -> dict[str, str]:
    out: dict[str, str] = {}
    for name, (kind, csv) in _CSV.items():
        body = {"name": name, "kind": kind, "risk_profile": "moderado", "csv": csv}
        response = client.post(f"{API_PREFIX}/portfolios/import", json=body)
        assert response.status_code == 201, response.text
        out[name] = response.json()["portfolio"]["id"]
    return out


def _ask(
    client: TestClient, question: str, focus: str | None = None, channel: str = "text"
) -> list[dict[str, Any]]:
    body = {"question": question, "channel": channel, "session_id": "ses_multi"}
    path = f"/portfolios/{focus}/ask" if focus else "/ask"
    response = client.post(f"{API_PREFIX}{path}", json=body)
    assert response.status_code == 200, response.text
    events = [json.loads(f.removeprefix("data: ")) for f in response.text.split("\n\n") if f]
    for event in events:
        _ADAPTER.validate_python(event)
    assert events[0]["type"] == "meta" and events[-1]["type"] == "done", events[-1]
    return events


def _sentences(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [e for e in events if e["type"] == "sentence"]


def _total(portfolio_id: str) -> str:
    fact = context.get(portfolio_id).fact("total")
    assert fact is not None
    return fact.display


def _install(*outcomes: Any) -> FakeStreamingClaude:
    fake = FakeStreamingClaude(*outcomes)
    claude.set_client(fake)
    return fake


@pytest.mark.parametrize("channel", ["text", "voice"])
def test_asks_about_another_portfolio_than_the_chosen_one(
    client: TestClient, ids: dict[str, str], channel: str
) -> None:
    hijos = ids["Hijos"]
    fake = _install(Reply(f"La cartera de tus hijos vale {_total(hijos)}."))

    events = _ask(client, "¿Cómo va la cartera de mis hijos?", ids["Personal"], channel)

    [sentence] = _sentences(events)
    assert sentence["portfolio_ids"] == [hijos]
    assert sentence["calc_ids"], "la cifra lleva su traza"
    assert events[-1]["fallback_used"] is False
    user = fake.messages.calls[0]["messages"][0]["content"][0]["text"]
    assert "<contexto_otras_carteras>" in user and hijos in user


def test_figure_of_another_portfolio_is_blocked_and_retried(
    client: TestClient, ids: dict[str, str]
) -> None:
    hijos = ids["Hijos"]
    wrong = f"Tu cartera Personal vale {_total(hijos)}."
    right = f"La de tus hijos vale {_total(hijos)}."
    fake = _install(Reply(wrong), Reply(right))

    events = _ask(client, "¿Cómo va la de mis hijos?", ids["Personal"])

    assert [s["text"] for s in _sentences(events)] == [right]
    assert events[-1]["blocked_count"] == 1
    feedback = fake.messages.calls[1]["messages"][0]["content"][-1]["text"]
    assert "«Hijos»" in feedback


def test_all_portfolios_answer_one_by_one_without_total(
    client: TestClient, ids: dict[str, str]
) -> None:
    events = _ask(client, "¿Cómo van mis carteras?")  # sin clave: plantilla

    sentences = _sentences(events)
    owners = [s["portfolio_ids"] for s in sentences]
    assert all(len(owner) == 1 for owner in owners)
    assert len({owner[0] for owner in owners}) == len(owners) >= 3
    assert {ids["Personal"], ids["Negocio"], ids["Hijos"]} <= {o[0] for o in owners}
    assert all(s["calc_ids"] for s in sentences)


def test_sum_across_portfolios_is_blocked(client: TestClient, ids: dict[str, str]) -> None:
    totals = [context.get(ids[name]).fact("total") for name in ("Personal", "Negocio")]
    total = sum((f.value for f in totals if f is not None), Decimal(0))
    summed = Reply(f"Entre todas tienes {format_eur(total)}.")
    _install(summed, summed)

    events = _ask(client, "¿Cuánto tengo en Personal y Negocio?")

    assert events[-1]["blocked_count"] == 2
    assert events[-1]["fallback_used"] is True
    texts = " ".join(s["text"] for s in _sentences(events))
    assert format_eur(total) not in texts
    assert all(len(s["portfolio_ids"]) == 1 for s in _sentences(events))


def test_one_sentence_with_figures_of_two_portfolios_is_blocked(
    client: TestClient, ids: dict[str, str]
) -> None:
    personal, negocio = _total(ids["Personal"]), _total(ids["Negocio"])
    mixed = f"Personal vale {personal} y Negocio vale {negocio}."
    split = f"Personal vale {personal}. Negocio vale {negocio}."
    fake = _install(Reply(mixed), Reply(split))

    events = _ask(client, "¿Cuánto valen Personal y Negocio?")

    assert [s["portfolio_ids"] for s in _sentences(events)] == [[ids["Personal"]], [ids["Negocio"]]]
    feedback = fake.messages.calls[1]["messages"][0]["content"][-1]["text"]
    assert "varias carteras" in feedback


def test_ambiguous_question_asks_which_portfolio(client: TestClient, ids: dict[str, str]) -> None:
    events = _ask(client, "¿Cómo va mi cartera?")  # sin cartera elegida ni nombrada

    [sentence] = _sentences(events)
    assert "«Hijos»" in sentence["text"] and "«Negocio»" in sentence["text"]
    assert sentence["calc_ids"] == []  # sin cifras: solo nombra las carteras
    assert set(ids.values()) <= set(sentence["portfolio_ids"])


def test_tools_can_read_any_portfolio(client: TestClient, ids: dict[str, str]) -> None:
    negocio = ids["Negocio"]
    answer = f"Tu cartera Negocio vale {_total(negocio)}."
    fake = _install(Reply(tool_uses=[("get_portfolio", {"portfolio_id": negocio})]), Reply(answer))

    events = _ask(client, "¿Y la otra?", ids["Personal"])

    [sentence] = _sentences(events)
    assert sentence["portfolio_ids"] == [negocio] and sentence["calc_ids"]
    result = fake.messages.calls[1]["messages"][-1]["content"][0]
    cartera = json.loads(result["content"])["cartera"]
    assert cartera == {"portfolio_id": negocio, "nombre": "Negocio"}


def test_new_data_tools_answer_for_the_given_portfolio(
    client: TestClient, ids: dict[str, str]
) -> None:
    names = {item.id: item.name for item in portfolio_service.list_portfolios()}
    for tool in ("get_status", "get_news", "get_alerts", "get_radar", "get_agenda"):
        result = tools.run(ids["Hijos"], tool, {"portfolio_id": "laura"}, names)
        assert not result.is_error, (tool, result.content)
        assert result.portfolio_id == "laura"
    listing = json.loads(tools.run(ids["Hijos"], "list_portfolios", {}).content)["result"]
    assert {row["nombre"] for row in listing} >= set(ids)
    # Sin plan, el radar da un error controlado (bloqueo «cartera sin plan»), nunca cifras.
    radar = tools.run(None, "get_radar", {"portfolio_id": ids["Hijos"]}, names)
    assert radar.is_error and radar.facts == []


def test_unknown_or_missing_portfolio_is_a_tool_error(ids: dict[str, str]) -> None:
    names = {pid: name for name, pid in ids.items()}
    missing = tools.run(None, "get_portfolio", {}, names)
    unknown = tools.run(None, "get_portfolio", {"portfolio_id": "pf_nope"}, names)
    assert missing.is_error and "falta `portfolio_id`" in missing.content
    assert unknown.is_error and "Hijos" in unknown.content
