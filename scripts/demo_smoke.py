"""Smoke del guion de demo por API (T2-03): recorre los pasos 1 a 8 contra el backend real.

Con el backend levantado y `DEMO_CLOCK` fijado (`make up`, ver `.env.example`):

    cd backend && uv run python ../scripts/demo_smoke.py [--url http://localhost:8000]

Resetea la demo, así que borra lo que hubiera. Sale con código 1 en el primer paso que falle. No
necesita clave de Claude: sin ella, el analizador usa el respaldo y el explicador, las plantillas.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from decimal import Decimal
from typing import Any

import httpx

API = "/api/v1"
LAURA = "laura"
JAVIER = "javier"
LIVE_EVENT = "nvda-2025-02"
PRELOADED = {"bce-2025-06", "oil-2025-06"}
MAX_TRACES = 40


class SmokeError(Exception):
    """Un paso del guion no cumple lo esperado."""


def _require(condition: object, message: str) -> None:
    if not condition:
        raise SmokeError(message)


def _call(client: httpx.Client, method: str, path: str, **kwargs: Any) -> Any:
    response = client.request(method, f"{API}{path}", **kwargs)
    _require(
        response.status_code == 200,
        f"{method} {path} devolvió {response.status_code}: {response.text[:300]}",
    )
    return response.json()


def _get(client: httpx.Client, path: str) -> Any:
    return _call(client, "GET", path)


def _ask(client: httpx.Client, portfolio: str, question: str) -> list[dict[str, Any]]:
    """Hace la pregunta y comprueba que el turno SSE llega completo y con frases."""
    response = client.post(
        f"{API}/portfolios/{portfolio}/ask",
        json={"question": question, "channel": "text", "session_id": f"smoke-{portfolio}"},
    )
    _require(response.status_code == 200, f"/ask devolvió {response.status_code}")
    events = [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]
    kinds = [event["type"] for event in events]
    _require("error" not in kinds, f"«{question}»: el turno acabó en error: {events[-1]}")
    _require(kinds[:1] == ["meta"] and kinds[-1:] == ["done"], f"«{question}»: turno roto: {kinds}")
    sentences = [event for event in events if event["type"] == "sentence"]
    _require(sentences, f"«{question}»: respuesta sin frases")
    return sentences


def _impact(client: httpx.Client, portfolio: str, event_id: str) -> dict[str, Any]:
    events = _get(client, f"/portfolios/{portfolio}/events")
    found = [event for event in events if event["event_id"] == event_id]
    _require(found, f"{portfolio}: falta el impacto de {event_id}")
    return dict(found[0])


def _status(client: httpx.Client, portfolio: str) -> dict[str, Any]:
    return dict(_get(client, f"/portfolios/{portfolio}/status"))


def step_1_tranquilo(client: httpx.Client) -> str:
    reset = _call(client, "POST", "/demo/reset", json={"preload": True})
    _require(
        PRELOADED <= set(reset["preloaded_event_ids"]),
        f"reset sin precarga: {reset['preloaded_event_ids']}",
    )
    status = _status(client, LAURA)
    _require(status["state"] == "tranquilo", f"Laura arranca en {status['state']}")
    _require(not _get(client, f"/portfolios/{LAURA}/alerts"), "Laura arranca con avisos")
    return f"Laura en {status['state_label']}"


def step_2_radiography(client: httpx.Client) -> str:
    exposure = _get(client, f"/portfolios/{LAURA}/exposure")
    radiography = exposure["radiography"]
    _require(radiography["num_holdings"] == 3, f"holdings: {radiography['num_holdings']}")
    _require(Decimal(exposure["coverage_pct"]) >= Decimal("0.9"), "cobertura < 90 %")
    _require(radiography["top_country"]["key"] == "US", radiography["top_country"])
    _require(Decimal(radiography["top_companies_group"]["weight"]) > 0, "sin peso en empresas")
    return (
        f"{radiography['top_country']['label']} {radiography['top_country']['weight']}, "
        f"{radiography['top_companies_group']['n']} empresas "
        f"{radiography['top_companies_group']['weight']}"
    )


def step_3_replay(client: httpx.Client) -> str:
    before = Decimal(_status(client, LAURA)["total_eur"])
    replay = _call(client, "POST", f"/demo/replay/{LIVE_EVENT}", json={})
    _require({LAURA, JAVIER} <= set(replay["portfolios"]), f"replay: {replay['portfolios']}")

    status = _status(client, LAURA)
    _require(status["state"] == "atento", f"tras el replay Laura está en {status['state']}")
    _require(Decimal(status["total_eur"]) < before, "el patrimonio no baja tras el evento")

    alerts = _get(client, f"/portfolios/{LAURA}/alerts")
    matching = [
        alert
        for alert in alerts
        if alert["event_id"] == LIVE_EVENT and alert["kind"] == "event_impact"
    ]
    _require(len(matching) == 1, f"avisos de {LIVE_EVENT}: {len(matching)}")
    _require(matching[0]["calc_id"], "el aviso no lleva calc_id")
    return f"Atento, {before} -> {status['total_eur']} EUR, 1 aviso"


def step_4_why_down(client: httpx.Client) -> str:
    sentences = _ask(client, LAURA, "¿Por qué ha bajado?")
    for sentence in sentences:
        for calc_id in sentence["calc_ids"]:
            _get(client, f"/traces/{calc_id}")
    return f"{len(sentences)} frases"


def step_5_panel(client: httpx.Client) -> str:
    events = _get(client, f"/portfolios/{LAURA}/events")
    event_ids = {event["event_id"] for event in events}
    _require(PRELOADED | {LIVE_EVENT} <= event_ids, f"eventos del panel: {sorted(event_ids)}")
    for event in events:
        low, central, high = (
            Decimal(event["low_eur"]),
            Decimal(event["impact_eur"]),
            Decimal(event["high_eur"]),
        )
        _require(
            low < high and low <= central <= high,
            f"{event['event_id']}: rango {low} / {central} / {high}. ¿Faltan las betas?",
        )
        _require(event["causal_chain"], f"{event['event_id']}: sin cadena causal")

    radar = _get(client, f"/portfolios/{LAURA}/radar")["items"]
    kinds = {item["kind"] for item in radar}
    _require({"risk", "opportunity"} <= kinds, f"radar sin riesgos y oportunidades: {kinds}")
    agenda = _get(client, f"/portfolios/{LAURA}/agenda")
    _require(agenda, "agenda vacía")
    return f"{len(events)} eventos, {len(radar)} avisos de radar, {len(agenda)} citas de agenda"


def step_6_two_portfolios(client: httpx.Client) -> str:
    laura = _impact(client, LAURA, LIVE_EVENT)
    javier = _impact(client, JAVIER, LIVE_EVENT)
    _require(
        laura["impact_eur"] != javier["impact_eur"],
        f"mismo impacto en las dos carteras: {laura['impact_eur']}",
    )
    return f"Laura {laura['impact_eur']} EUR, Javier {javier['impact_eur']} EUR"


def step_7_on_track(client: httpx.Client) -> str:
    projection = _get(client, f"/portfolios/{LAURA}/projection")
    _require(projection["on_track"] is True, "Laura no va en plan")
    sentences = _ask(client, LAURA, "¿Voy bien?")
    return f"on_track, {len(sentences)} frases"


def step_8_trace(client: httpx.Client) -> str:
    """Recorre la cadena de `parent_calc_ids` del impacto hasta el final."""
    root = _impact(client, LAURA, LIVE_EVENT)["calc_id"]
    pending, seen, sources = [root], set[str](), 0
    while pending and len(seen) < MAX_TRACES:
        calc_id = pending.pop()
        if calc_id in seen:
            continue
        seen.add(calc_id)
        trace = _get(client, f"/traces/{calc_id}")
        sources += len(trace["sources"])
        pending.extend(trace["parent_calc_ids"])
    _require(len(seen) > 1, "la traza del impacto no tiene padres")
    _require(sources, "ninguna traza de la cadena lleva fuentes")
    return f"{len(seen)} cálculos, {sources} fuentes"


STEPS: tuple[tuple[str, Callable[[httpx.Client], str]], ...] = (
    ("1 Tranquilo", step_1_tranquilo),
    ("2 Radiografía", step_2_radiography),
    ("3 Replay, Atento y aviso", step_3_replay),
    ("4 ¿Por qué ha bajado?", step_4_why_down),
    ("5 Panel", step_5_panel),
    ("6 Dos carteras", step_6_two_portfolios),
    ("7 ¿Voy bien?", step_7_on_track),
    ("8 Traza", step_8_trace),
)


def run(client: httpx.Client, report: Callable[[str], None] = print) -> None:
    """Ejecuta el guion en orden. Lanza `SmokeError` en el primer paso que falle."""
    for name, step in STEPS:
        try:
            detail = step(client)
        except SmokeError as error:
            raise SmokeError(f"Paso {name}: {error}") from error
        report(f"OK  {name}: {detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--url", default="http://localhost:8000", help="base del backend")
    args = parser.parse_args()
    with httpx.Client(base_url=args.url, timeout=60) as client:
        try:
            run(client)
        except (SmokeError, httpx.HTTPError) as error:
            print(f"FALLO  {error}", file=sys.stderr)
            return 1
    print("Guion completo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
