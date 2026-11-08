"""Reloj inyectable (D-031). Todo el backend usa `now()`; nunca `datetime.now()`.

En modo demo el reloj se fija con `DEMO_CLOCK` o con `PUT /demo/clock` (que llama a `set_now`).
"""

from datetime import UTC, datetime

from app.config import get_settings

_fixed: datetime | None = None
_override_set = False


def now() -> datetime:
    """Instante actual en UTC (o el fijado para la demo)."""
    if _override_set:
        return _fixed if _fixed is not None else datetime.now(UTC)
    configured = get_settings().demo_clock
    if configured is not None:
        return configured.astimezone(UTC)
    return datetime.now(UTC)


def set_now(value: datetime | None) -> None:
    """Fija el reloj (`value`) o vuelve al reloj real (`None`). Tiene prioridad sobre DEMO_CLOCK."""
    global _fixed, _override_set
    if value is not None:
        if value.tzinfo is None:
            raise ValueError("El reloj necesita una fecha con zona horaria")
        value = value.astimezone(UTC)
    _fixed = value
    _override_set = True


def reset() -> None:
    """Olvida cualquier `set_now` y vuelve a respetar DEMO_CLOCK. Útil en tests."""
    global _fixed, _override_set
    _fixed = None
    _override_set = False
