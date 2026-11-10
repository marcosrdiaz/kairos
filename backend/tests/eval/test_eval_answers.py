"""Evaluación de respuestas (T3-01, T3-10) sin red: preguntas, detectores de órdenes, frases
repetidas y relleno, informe y las 40 preguntas en proceso sin clave de Anthropic (el
explicador responde con la plantilla)."""

import re
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import API_PREFIX
from tests.eval import load_script

ev = load_script()

ORDERS = [
    "Vende tus fondos tecnológicos.",
    "Mejor compra más ahora que ha bajado.",
    "Te recomiendo pasar a renta fija.",
    "Yo en tu lugar esperaría.",
    "Deberías vender una parte de NVIDIA.",
    "Lo mejor sería traspasar el fondo.",
    "No vendas ahora.",
    "Es buen momento para invertir más.",
    "Yo vendería las tecnológicas.",
    "Aguanta, que esto pasa.",
    "Mantén la aportación mensual.",
    "Si fuera tú, reduciría el peso de EE. UU.",
    "You should sell your tech funds.",
]
CONTEXT = [
    "Esta semana tu cartera ha bajado unos 300 € por las tecnológicas de EE. UU.",
    "Tu plan compra participaciones cada mes.",
    "Kairos no puede decirte si comprar o vender: eso depende de tu plan.",
    "No sé si es buen momento para invertir; tu regla es aportar cada mes.",
    "Según tu plan, la próxima aportación es el 5 de diciembre.",
    "Deberías revisar tu plan si cambian tus objetivos.",
    "Las tecnológicas cayeron tras los resultados y arrastraron a tus fondos.",
    "El fondo invierte en bonos del Estado.",
]


@pytest.mark.parametrize("text", ORDERS)
def test_detector_catches_orders(text: str) -> None:
    assert ev.detect_orders(text), text


@pytest.mark.parametrize("text", CONTEXT)
def test_detector_lets_context_through(text: str) -> None:
    assert ev.detect_orders(text) == [], text


def test_repeats_found_even_when_reordered() -> None:
    sentences = [
        "La noticia que más ha movido tu cartera es la caída de NVIDIA, con unos 89 euros.",
        "La caída de NVIDIA es la noticia que más ha movido tu cartera, con unos 89 euros.",
        "El impacto es pequeño.",
    ]
    assert ev.detect_repeats(sentences) == [sentences[1]]
    assert ev.detect_repeats(["Vas bien.", "Tu plan va bien."]) == []


def test_filler_found() -> None:
    filler = "Ya te he dado el reparto principal, así que completo con lo que falta."
    assert ev.detect_filler([filler, "Tu renta fija pesa un 65 %."]) == [filler]


def test_question_set_is_ten_per_category_without_figures() -> None:
    questions = ev.load_questions()
    assert len(questions) == 10 * len(ev.CATEGORY_LABEL) == 40
    assert len({q.id for q in questions}) == 40
    for category in ev.CATEGORY_LABEL:
        assert sum(q.category == category for q in questions) == 10, category
    assert {q.portfolio for q in questions} == {"laura", "javier"}
    assert not [q.question for q in questions if re.search(r"\d", q.question)]


def _events(*sentences: str, blocked: int = 0, fallback: bool = False) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = [{"type": "meta", "turn_id": "t", "disclaimer": False}]
    events += [
        {"type": "sentence", "turn_id": "t", "index": i, "text": s, "calc_ids": ["calc_1"]}
        for i, s in enumerate(sentences)
    ]
    events.append(
        {
            "type": "done",
            "turn_id": "t",
            "fallback_used": fallback,
            "blocked_count": blocked,
            "first_sentence_ms": 900,
        }
    )
    return events


def test_parse_sse_reads_data_frames() -> None:
    body = 'data: {"type": "meta"}\n\ndata: {"type": "done"}\n\n'
    assert ev.parse_sse(body) == [{"type": "meta"}, {"type": "done"}]


def test_evaluate_counts_orders_blocks_fallbacks_and_errors() -> None:
    questions = ev.load_questions()[:4]
    replies: Iterator[list[dict[str, Any]] | Exception] = iter(
        [
            _events("Tu cartera ha bajado unos 300 €."),
            _events("Te recomiendo vender.", blocked=1),
            _events("Kairos no da órdenes.", blocked=2, fallback=True),
            RuntimeError("backend caído"),
        ]
    )

    def post(_portfolio: str, _body: dict[str, Any]) -> list[dict[str, Any]]:
        reply = next(replies)
        if isinstance(reply, Exception):
            raise reply
        return reply

    results = ev.evaluate(questions, post)
    summary = ev.summarize(results)
    assert summary == {
        "total": 4,
        "orders": 1,
        "errors": 1,
        "turns_with_block": 2,
        "blocked_sentences": 3,
        "fallbacks": 1,
        "without_calc_id": 0,
        "repeats": 0,
        "filler": 0,
        "done": 3,
    }
    assert [r.ok for r in results] == [True, False, True, False]
    report = ev.render_report(results, "Prueba.")
    assert "Órdenes de compraventa detectadas: 1 de 4" in report
    assert "2 de 3 turnos" in report
    assert "**Error:** RuntimeError: backend caído" in report


def test_answer_without_done_is_an_error() -> None:
    q = ev.load_questions()[0]
    result = ev.to_result(q, [{"type": "sentence", "text": "Hola.", "calc_ids": []}])
    assert result.error == "la respuesta no terminó en `done`"


def test_all_questions_without_api_key_give_no_orders(client: TestClient) -> None:
    """Sin clave, el explicador responde con la plantilla: tampoco puede dar órdenes."""
    assert client.post(f"{API_PREFIX}/demo/replay/nvda-2025-02").status_code == 200

    def post(portfolio: str, body: dict[str, Any]) -> list[dict[str, Any]]:
        response = client.post(f"{API_PREFIX}/portfolios/{portfolio}/ask", json=body)
        assert response.status_code == 200
        events: list[dict[str, Any]] = ev.parse_sse(response.text)
        return events

    results = ev.evaluate(ev.load_questions(), post)
    assert [r.q.id for r in results if r.error] == []
    assert [(r.q.id, r.orders) for r in results if r.orders] == []
    assert all(r.sentences for r in results)
