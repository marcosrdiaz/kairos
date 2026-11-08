"""Contrato de `POST /demo/reset` (diseño del MVP §4.6). Solo con `DEMO_MODE=true`.

El resto del control de demo vive en su módulo: `ReplayOut` en `schemas/events.py`.
"""

from pydantic import Field

from app.schemas.common import ContractModel


class DemoResetRequest(ContractModel):
    """Cuerpo opcional. Con `preload: true` (lo que usa el guion) se reproducen además BCE y
    petróleo con `occurred_at = now() − 96 h` y `silent: true`."""

    preload: bool = False


class DemoResetOut(ContractModel):
    """Qué ha recargado el reset: carteras en su estado inicial y eventos precargados."""

    portfolio_ids: list[str]
    preloaded_event_ids: list[str] = Field(default_factory=list)
