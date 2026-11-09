"""Umbrales de los avisos (D-032). T3-04 los calibra con datos reales.

`MIN_EUR` y `MIN_SHARE` son los mismos que el estado «atento» del widget (`status.config`): un test
(`test_alerts_engine.py`) comprueba que no se desincronizan. Si cambias uno, cambia el otro.
"""

from decimal import Decimal

MIN_EUR = Decimal("150")
MIN_SHARE = Decimal("0.005")
"""Aviso si |impacto| ≥ max(`MIN_EUR`, `MIN_SHARE` del patrimonio), es decir, `score ≥ 1`."""

WEEKLY_LIMIT = 2
"""Avisos por semana ISO y cartera. Los `dca_pending` no cuentan."""

IMPACT_LOOKBACK_DAYS = 3650
"""Ventana para buscar el impacto de un evento: se filtra por fecha de cálculo, no de evento."""
