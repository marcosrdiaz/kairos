"""Agenda de próximos eventos: funciones puras (T2-06, diseño del MVP §4.3, D-080).

Sin BD: `service.get_agenda` reúne la valoración, las betas y el look-through y llama aquí.
- Fecha de cada cita: el día del reloj de demo + `offset_days`, a la hora `time_utc`.
- Exposición a un factor: Σ V_i de las posiciones con |β_{i,f}| ≥ 0,1.
- Exposición a los resultados de una empresa: Σ V_i × peso de la empresa en i (look-through).
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from app.schemas.common import Factor
from app.schemas.events import EventType
from app.schemas.portfolio import Frequency

AGENDA_FILE = Path(__file__).resolve().parents[3] / "data" / "events" / "agenda.json"
"""En local, `<repo>/data/events/agenda.json`; en Docker, `/data/events/agenda.json`."""
AGENDA_REF = "data/events/agenda.json"

BETA_THRESHOLD = Decimal("0.1")
WEIGHT_STEP = Decimal("0.0001")
ZERO = Decimal("0")


@dataclass(frozen=True)
class AgendaEvent:
    id: str
    offset_days: int
    time_utc: str
    kind: EventType
    title: str
    factor: Factor
    company: str | None


def load_events(path: Path = AGENDA_FILE) -> list[AgendaEvent]:
    """Lee `agenda.json` (formato de D-080)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        AgendaEvent(
            id=raw["id"],
            offset_days=int(raw["offset_days"]),
            time_utc=raw["time_utc"],
            kind=EventType(raw["kind"]),
            title=raw["title"],
            factor=Factor(raw["factor"]),
            company=raw.get("company"),
        )
        for raw in data["events"]
    ]


def event_date(now: datetime, offset_days: int, time_utc: str) -> datetime:
    """Día de `now` (en UTC) + `offset_days`, a la hora `HH:MM` UTC."""
    day = now.astimezone(UTC).date() + timedelta(days=offset_days)
    return datetime.combine(day, time.fromisoformat(time_utc), tzinfo=UTC)


def factor_exposure(
    values: Mapping[str, Decimal],
    betas: Mapping[str, Mapping[Factor, Decimal]],
    factor: Factor,
    threshold: Decimal = BETA_THRESHOLD,
) -> Decimal:
    """Σ V_i de las posiciones con |β_{i,factor}| ≥ `threshold`. Sin beta, la posición no cuenta."""
    return sum(
        (
            value
            for asset_id, value in values.items()
            if abs(betas.get(asset_id, {}).get(factor, ZERO)) >= threshold
        ),
        ZERO,
    )


def company_exposure(
    values: Mapping[str, Decimal],
    weights: Mapping[str, Mapping[str, Decimal]],
    company: str,
) -> Decimal:
    """Σ V_i × peso de `company` en la posición i (1 si es la propia acción)."""
    return sum(
        (
            value * weights.get(asset_id, {}).get(company, ZERO)
            for asset_id, value in values.items()
        ),
        ZERO,
    )


def exposed_weight(exposed_eur: Decimal, total_eur: Decimal) -> Decimal:
    """Fracción de la cartera expuesta, a 4 decimales. Cero si la cartera vale cero."""
    if total_eur == ZERO:
        return ZERO
    return (exposed_eur / total_eur).quantize(WEIGHT_STEP)


def dca_title(frequency: Frequency) -> str:
    return "Tu aportación mensual" if frequency is Frequency.MONTHLY else "Tu aportación semanal"
