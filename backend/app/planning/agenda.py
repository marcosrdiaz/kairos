"""Agenda de próximos eventos: funciones puras (T2-06, diseño del MVP §4.3, D-080).

Sin BD: `service.get_agenda` reúne la valoración, las betas y el look-through y llama aquí.
- Fecha de cada cita: el día del reloj de demo + `offset_days`, a la hora `time_utc`.
- Exposición a un factor: Σ V_i de las posiciones con |β_{i,f}| ≥ umbral del factor y
  |β_{i,f}| ≥ 2·error estándar (ver `BETA_THRESHOLDS`). El diseño §4.3 decía |β| ≥ 0,1 para
  todos; se cambió porque cada factor tiene sus unidades (decisión de T2-06).
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

BETA_THRESHOLDS: dict[Factor, Decimal] = {
    Factor.EQ_GLOBAL: Decimal("0.12"),
    Factor.EQ_US_TECH: Decimal("0.08"),
    Factor.RATES_EUR: Decimal("2.5"),
    Factor.OIL: Decimal("0.04"),
    Factor.EURUSD: Decimal("0.24"),
}
"""|β| mínima por factor: la que hace que un día normal del factor (1σ de su variación diaria en
`data/factors`, 2023-11 a 2026-11) mueva el activo al menos un 0,1 %. Es 0,001 / σ_diaria,
redondeado: EQ_GLOBAL 0,82 %, EQ_US_TECH 1,32 %, RATES_EUR 4,1 pb, OIL 2,51 %, EURUSD 0,42 %.
Un umbral único (0,1) no sirve porque cada factor tiene sus unidades."""
MIN_T_STAT = Decimal("2")
"""Además, |β| ≥ 2·error estándar: con menos, la beta no se distingue de cero."""
WEIGHT_STEP = Decimal("0.0001")
ZERO = Decimal("0")

BetaWithError = tuple[Decimal, Decimal]
"""(β, error estándar) de un activo frente a un factor."""


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


def is_exposed(estimate: BetaWithError, factor: Factor) -> bool:
    """|β| ≥ umbral del factor y |β| ≥ 2·error estándar (la beta no es ruido)."""
    beta, std_err = estimate
    return abs(beta) >= BETA_THRESHOLDS[factor] and abs(beta) >= MIN_T_STAT * std_err


def factor_exposure(
    values: Mapping[str, Decimal],
    betas: Mapping[str, Mapping[Factor, BetaWithError]],
    factor: Factor,
) -> Decimal:
    """Σ V_i de las posiciones expuestas al factor (`is_exposed`). Sin beta, no cuenta."""
    return sum(
        (
            value
            for asset_id, value in values.items()
            if (estimate := betas.get(asset_id, {}).get(factor)) is not None
            and is_exposed(estimate, factor)
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
