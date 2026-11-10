"""Comprueba el catálogo (`data/seed/assets.json`) contra Yahoo Finance (T4-26).

Para cada activo con `price_source` `yahoo:<símbolo>`:

- Yahoo responde y la divisa de cotización es la del catálogo (EUR o USD: el único tipo de
  cambio en directo es EUR/USD).
- Hay al menos 2 años de cierres (las betas usan 3; con menos, el activo sale «sin betas»).
- El último cierre no tiene más de 7 días (el símbolo sigue cotizando).

Sale con código 1 si algún activo falla. Necesita red; en CI lo lanza un test `live`.

    cd backend && uv run python ../scripts/check_catalog.py
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parent.parent
ASSETS_PATH = ROOT / "data" / "seed" / "assets.json"
CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
SUPPORTED_CURRENCIES = {"EUR", "USD"}
MIN_SESSIONS = 500  # unos 2 años
MAX_STALE = timedelta(days=7)


@dataclass(frozen=True)
class Check:
    asset_id: str
    symbol: str
    problems: list[str]


def check_chart(asset: dict[str, Any], payload: dict[str, Any], today: date) -> list[str]:
    """Problemas de un activo a partir de la respuesta de Yahoo (función pura, para tests)."""
    try:
        result = payload["chart"]["result"][0]
        meta = result["meta"]
        stamps = result.get("timestamp") or []
        closes = result["indicators"]["quote"][0].get("close") or []
    except (KeyError, IndexError, TypeError):
        return ["Yahoo no devuelve datos"]
    problems = []
    currency = meta.get("currency")
    if currency not in SUPPORTED_CURRENCIES:
        problems.append(f"divisa {currency!r}: solo EUR o USD")
    elif currency != asset["currency"]:
        problems.append(f"divisa {currency} en Yahoo y {asset['currency']} en el catálogo")
    sessions = [
        datetime.fromtimestamp(int(s), UTC).date()
        for s, c in zip(stamps, closes, strict=False)
        if c is not None
    ]
    if len(sessions) < MIN_SESSIONS:
        problems.append(f"solo {len(sessions)} sesiones (mínimo {MIN_SESSIONS})")
    if not sessions or today - max(sessions) > MAX_STALE:
        last = max(sessions).isoformat() if sessions else "ninguno"
        problems.append(f"último cierre {last}: no cotiza")
    return problems


def run(http: httpx.Client, today: date) -> list[Check]:
    assets = json.loads(ASSETS_PATH.read_text(encoding="utf-8"))["assets"]
    checks = []
    for asset in assets:
        source = str(asset["price_source"])
        if not source.startswith("yahoo:"):
            continue
        symbol = source.removeprefix("yahoo:")
        try:
            response = http.get(
                CHART_URL.format(symbol=symbol), params={"range": "3y", "interval": "1d"}
            )
            response.raise_for_status()
            problems = check_chart(asset, response.json(), today)
        except (httpx.HTTPError, ValueError) as error:
            problems = [f"Yahoo no responde: {error}"]
        checks.append(Check(asset["id"], symbol, problems))
    return checks


def main() -> int:
    with httpx.Client(timeout=15, headers={"User-Agent": "Mozilla/5.0"}) as http:
        checks = run(http, datetime.now(UTC).date())
    failed = [c for c in checks if c.problems]
    for c in checks:
        status = "OK " if not c.problems else "MAL"
        print(f"{status} {c.asset_id:<14} {c.symbol:<16} {'; '.join(c.problems)}")
    print(f"{len(checks) - len(failed)}/{len(checks)} activos consultables en Yahoo")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
