"""Umbrales del estado del widget (`SPEC.md` §8.6). T3-04 los calibra con datos reales."""

from datetime import timedelta
from decimal import Decimal

from app.schemas.agents import StatusState

ATENTO_WINDOW = timedelta(hours=72)
ATENTO_MIN_EUR = Decimal("150")
ATENTO_MIN_SHARE = Decimal("0.005")
"""`atento` si |impacto| ≥ max(`ATENTO_MIN_EUR`, `ATENTO_MIN_SHARE` del patrimonio)."""

REFRESH_S = 10.0
"""Cada cuánto `GET /status` comprueba si han cambiado los datos sin que llegue un evento: una
operación del usuario o el cierre de la ventana de 72 h."""

LABELS: dict[StatusState, str] = {
    StatusState.TRANQUILO: "Tranquilo",
    StatusState.ATENTO: "Atento",
    StatusState.REVISA_PLAN: "Revisa tu plan",
}
