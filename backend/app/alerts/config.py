"""Umbrales de los avisos (D-032). Calibrados con datos reales en T3-04: se mantienen (ver la
decisión de calibración de umbrales de T3-04).

`MIN_EUR` y `MIN_SHARE` son los mismos que el estado «atento» del widget (`status.config`): un test
(`test_alerts_engine.py`) comprueba que no se desincronizan. Si cambias uno, cambia el otro.
"""

from datetime import timedelta
from decimal import Decimal

MIN_EUR = Decimal("150")
MIN_SHARE = Decimal("0.005")
"""Aviso si |impacto| ≥ max(`MIN_EUR`, `MIN_SHARE` del patrimonio), es decir, `score ≥ 1`."""

WEEKLY_LIMIT = 2
"""Avisos por semana ISO y cartera. Los `dca_pending` no cuentan."""

MARKET_MOVE_IN_DEMO = False
"""Avisos `market_move` con `DEMO_MODE=true`. Apagados: gastarían el cupo semanal que el guion
necesita para el aviso del evento (paso 3). Los tests lo encienden."""

MARKET_MOVE_CHECK_EVERY = timedelta(minutes=15)
"""Cada cuánto se recalcula el movimiento del día de una cartera al leer sus avisos (el polling es
cada 5 s y `explain_move` deja una traza en cada llamada)."""

IMPACT_LOOKBACK_DAYS = 3650
"""Ventana para buscar el impacto de un evento: se filtra por fecha de cálculo, no de evento."""
