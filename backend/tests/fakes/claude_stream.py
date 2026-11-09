"""Cliente de Claude falso con streaming (`messages.stream`) para el explicador.

Cada llamada consume un resultado guionizado: una `Reply` (texto en trozos y, si se quiere,
llamadas a herramientas) o una excepción que lanzar. Registra los argumentos de cada llamada.
"""

import copy
from collections.abc import Iterator
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any


@dataclass
class Reply:
    text: str = ""
    tool_uses: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    stop_reason: str | None = None
    chunk: int = 7


class _Stream:
    def __init__(self, reply: Reply, number: int) -> None:
        self._reply = reply
        self._number = number
        self.consumed = 0

    def __enter__(self) -> "_Stream":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def __iter__(self) -> Iterator[SimpleNamespace]:
        text, size = self._reply.text, self._reply.chunk
        yield SimpleNamespace(type="message_start")
        for start in range(0, len(text), size):
            self.consumed = start + size
            yield SimpleNamespace(type="text", text=text[start : start + size])

    def get_final_message(self) -> SimpleNamespace:
        reply = self._reply
        content: list[SimpleNamespace] = []
        if reply.text:
            content.append(SimpleNamespace(type="text", text=reply.text))
        for i, (name, args) in enumerate(reply.tool_uses):
            tool_id = f"toolu_{self._number}_{i}"
            content.append(SimpleNamespace(type="tool_use", id=tool_id, name=name, input=args))
        stop = reply.stop_reason or ("tool_use" if reply.tool_uses else "end_turn")
        return SimpleNamespace(content=content, stop_reason=stop)


@dataclass
class _Messages:
    outcomes: list[Any]
    calls: list[dict[str, Any]] = field(default_factory=list)

    def stream(self, **kwargs: Any) -> _Stream:
        self.calls.append({**kwargs, "messages": copy.deepcopy(kwargs.get("messages"))})
        if not self.outcomes:
            raise AssertionError("FakeStreamingClaude: no quedan respuestas guionizadas")
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return _Stream(outcome, len(self.calls))


class FakeStreamingClaude:
    """`outcomes`, por orden de llamada: `Reply` o una excepción."""

    def __init__(self, *outcomes: Any) -> None:
        self.messages = _Messages(list(outcomes))
