"""Cliente de Claude falso: devuelve respuestas preparadas y registra las llamadas."""

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any


@dataclass
class _Messages:
    outcomes: list[Any]
    calls: list[dict[str, Any]] = field(default_factory=list)

    def parse(self, **kwargs: Any) -> SimpleNamespace:
        self.calls.append(kwargs)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        stop_reason = "refusal" if outcome is None else "end_turn"
        return SimpleNamespace(parsed_output=outcome, stop_reason=stop_reason)


class FakeClaude:
    """`outcomes`, por orden: la salida parseada, `None` (rechazo) o una excepción que lanzar."""

    def __init__(self, *outcomes: Any) -> None:
        self.messages = _Messages(list(outcomes))
