"""Caché del contexto precargado (`agents/context.py`): se reconstruye cuando cambia el
`calc_id` de `status`, al pasar el TTL o al invalidarla."""

from collections.abc import Iterator
from dataclasses import replace
from datetime import timedelta
from typing import Any

import pytest

from app.agents import context
from app.schemas import examples
from app.schemas.status import StatusOut
from app.status import service as status_service
from tests.fakes import explainer as fx


class _Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, Any]]:
    state: dict[str, Any] = {"builds": 0, "calc_id": "calc_status_a", "clock": _Clock()}

    def build(_pid: str, _state: object = None) -> context.Preloaded:
        state["builds"] += 1
        pre = fx.preloaded()
        update: dict[str, Any] = {}
        if "persona" in state:
            update["persona_hint"] = state["persona"]
        if state.get("volatile"):
            update["as_of"] = pre.context.as_of + timedelta(minutes=1)
            update["facts"] = [
                f.model_copy(update={"calc_id": "calc_nuevo"}) for f in pre.context.facts
            ]
        return replace(pre, context=pre.context.model_copy(update=update))

    def status(_pid: str) -> StatusOut:
        out = StatusOut.model_validate(examples.load("StatusOut"))
        return out.model_copy(update={"calc_id": state["calc_id"]})

    monkeypatch.setattr(context, "build", build)
    monkeypatch.setattr(context, "_monotonic", state["clock"])
    monkeypatch.setattr(status_service, "get_status", status)
    context.invalidate()
    yield state
    context.invalidate()


def test_cached_while_status_and_ttl_hold(env: dict[str, Any]) -> None:
    first = context.get("laura")
    env["clock"].now += context.TTL_S - 1
    assert context.get("laura") is first
    assert env["builds"] == 1


def test_rebuilt_after_ttl(env: dict[str, Any]) -> None:
    context.get("laura")
    env["clock"].now += context.TTL_S + 1
    env["persona"] = "otro perfil"
    assert context.get("laura").context.persona_hint == "otro perfil"
    assert env["builds"] == 2


def test_same_data_after_ttl_keeps_the_context_for_the_prompt_cache(env: dict[str, Any]) -> None:
    """Cada reconstrucción trae `calc_id` y `as_of` nuevos: si se usaran, el prompt cambiaría."""
    first = context.get("laura")
    env["clock"].now += context.TTL_S + 1
    env["volatile"] = True
    assert context.get("laura") is first
    assert env["builds"] == 2
    env["clock"].now += context.TTL_S - 1
    assert context.get("laura") is first
    assert env["builds"] == 2, "el TTL vuelve a contar desde la última comprobación"


def test_rebuilt_when_status_calc_id_changes(env: dict[str, Any]) -> None:
    first = context.get("laura")
    env["calc_id"] = "calc_status_b"
    assert context.get("laura") is not first
    assert env["builds"] == 2


def test_invalidate_one_portfolio_or_all(env: dict[str, Any]) -> None:
    context.get("laura")
    context.get("javier")
    context.invalidate("laura")
    context.get("laura")
    context.get("javier")
    assert env["builds"] == 3
    context.invalidate()
    context.get("javier")
    assert env["builds"] == 4
