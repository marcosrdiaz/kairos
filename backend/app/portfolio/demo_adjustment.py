"""Ajuste de demo tras un replay (D-031, decisión 17 del diseño). Solo con `DEMO_MODE=true`.

Los precios no se tocan: el impacto central estimado de cada posición se guarda aparte
(`demo_adjustment`, una fila por posición) y la valoración lo suma. `events` lo aplica tras
calcular el impacto y `/demo/reset` lo borra.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core import clock
from app.core.db import session_scope
from app.portfolio import repository
from app.portfolio.models import DemoAdjustment
from app.schemas.impact import EventImpactOut
from app.schemas.portfolio import DemoAdjustmentOut

LABEL = "Estimación tras el evento"
ZERO = Decimal(0)


@dataclass(frozen=True)
class AdjustmentRow:
    event_id: str
    asset_id: str
    impact_eur: Decimal
    calc_id: str


@dataclass(frozen=True)
class Summary:
    by_asset: dict[str, Decimal]
    """Ajuste en € por activo, para `engine.value_portfolio`."""
    by_event: list[DemoAdjustmentOut]
    """Lo que se muestra en `PortfolioOut.demo_adjustments`, en orden de replay."""


def apply(portfolio_id: str, impact: EventImpactOut) -> None:
    """Guarda el impacto de cada posición del `breakdown`; sustituye el de ese mismo evento."""
    if not get_settings().demo_mode:
        return
    now = clock.now()
    rows = [
        DemoAdjustment(
            portfolio_id=portfolio_id,
            event_id=impact.event_id,
            asset_id=asset.asset_id,
            impact_eur=asset.impact_eur,
            label=LABEL,
            calc_id=impact.calc_id,
            created_at=now,
        )
        for asset in impact.breakdown
    ]
    with session_scope() as session:
        repository.delete_demo_adjustments(session, portfolio_id, impact.event_id)
        repository.add_demo_adjustments(session, rows)


def clear(portfolio_id: str | None = None, event_id: str | None = None) -> None:
    """Sin argumentos, borra todos los ajustes."""
    with session_scope() as session:
        repository.delete_demo_adjustments(session, portfolio_id, event_id)


def load(session: Session, portfolio_id: str) -> list[AdjustmentRow]:
    """Filas de la cartera; vacío fuera del modo demo."""
    if not get_settings().demo_mode:
        return []
    return [
        AdjustmentRow(row.event_id, row.asset_id, row.impact_eur, row.calc_id)
        for row in repository.list_demo_adjustments(session, portfolio_id)
    ]


def summarize(rows: Iterable[AdjustmentRow], held: set[str]) -> Summary:
    """Agrega por activo y por evento. Ignora las filas de activos que ya no están en cartera."""
    by_asset: dict[str, Decimal] = {}
    by_event: dict[str, tuple[Decimal, str]] = {}
    for row in rows:
        if row.asset_id not in held:
            continue
        by_asset[row.asset_id] = by_asset.get(row.asset_id, ZERO) + row.impact_eur
        total, _ = by_event.get(row.event_id, (ZERO, row.calc_id))
        by_event[row.event_id] = (total + row.impact_eur, row.calc_id)
    return Summary(
        by_asset=by_asset,
        by_event=[
            DemoAdjustmentOut(event_id=event_id, impact_eur=total, label=LABEL, calc_id=calc_id)
            for event_id, (total, calc_id) in by_event.items()
        ],
    )
