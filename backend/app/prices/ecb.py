"""Cliente HTTP del BCE para el factor `RATES_EUR` en directo (T4-01).

Misma serie que `scripts/fetch_prices.py` (D-045): curva AAA del área euro a 10 años, sin clave.
El BCE publica en porcentaje; aquí se pasa a fracción con 12 decimales, como en
`data/factors/RATES_EUR.csv`. Los números se leen como `Decimal` (nunca `float`).
"""

import csv
import io
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation

import httpx

from app.core import clock
from app.prices.yahoo import ProviderError

RATES_URL = (
    "https://data-api.ecb.europa.eu/service/data/YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y"
    "?format=csvdata&startPeriod={start}"
)
SOURCE = "ecb:YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y"
TIMEOUT_S = 10.0
STEP = Decimal("0.000000000001")


def parse_rates(text: str, today: date) -> list[tuple[date, Decimal]]:
    """Filas `(fecha, rentabilidad en fracción)` anteriores a `today`, en orden de fecha. Puede
    ser negativa (como en 2020); los huecos se saltan."""
    rows: dict[date, Decimal] = {}
    try:
        for row in csv.DictReader(io.StringIO(text)):
            raw, day = (row.get("OBS_VALUE") or "").strip(), row.get("TIME_PERIOD") or ""
            if not raw:
                continue
            value = Decimal(raw)
            when = date.fromisoformat(day.strip())
            if value.is_finite() and when < today:
                rows[when] = (value / 100).quantize(STEP, ROUND_HALF_EVEN)
    except (ValueError, InvalidOperation) as error:
        raise ProviderError(f"BCE: respuesta no válida ({error})") from error
    return sorted(rows.items())


class EcbClient:
    def __init__(self, http: httpx.Client | None = None) -> None:
        self._http = http or httpx.Client(timeout=TIMEOUT_S, follow_redirects=True)

    def rates(self, start: date) -> list[tuple[date, Decimal]]:
        """Rentabilidades desde `start` hasta ayer (según `clock`)."""
        try:
            response = self._http.get(RATES_URL.format(start=start.isoformat()))
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise ProviderError(f"BCE: {error}") from error
        return parse_rates(response.text, clock.now().date())
