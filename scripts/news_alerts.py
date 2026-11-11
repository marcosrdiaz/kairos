"""Lanza ya los avisos por noticia (`news_estimate`, T4-31) de las carteras: `make news-alerts`.

En modo demo no se lanzan solos al leer los avisos (gastarían el cupo semanal que necesita el aviso
del evento del guion), así que la demo los reproduce con este script. Misma regla que en
producción: umbral según el perfil, límite semanal compartido y un aviso nuevo por cartera y día.
Tras `/demo/reset` se puede repetir y da lo mismo.

cd backend && uv run python ../scripts/news_alerts.py [--portfolio laura] [--now <instante>]

`--now`: si se ha movido el reloj con `PUT /demo/clock` (vive en la memoria del backend), el mismo
instante aquí. Sin él, `DEMO_CLOCK`, como el backend al arrancar.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

# En Docker el código está en /app (directorio de trabajo); en local, en <repo>/backend.
for candidate in (Path.cwd(), Path(__file__).resolve().parents[1] / "backend"):
    if (candidate / "app" / "__init__.py").is_file() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))
        break


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--portfolio", action="append", help="id de cartera (por defecto, todas)")
    parser.add_argument("--now", type=datetime.fromisoformat, help="instante del reloj (UTC)")
    args = parser.parse_args()

    from app.alerts import service as alerts_service
    from app.core import clock
    from app.portfolio import service as portfolio_service

    if args.now is not None:
        clock.set_now(args.now)
    portfolio_ids = args.portfolio or portfolio_service.list_portfolio_ids()
    for portfolio_id in portfolio_ids:
        changed = alerts_service.check_news(portfolio_id, force=True)
        print(f"{portfolio_id}: {changed} aviso(s) por noticia nuevos o rehechos")


if __name__ == "__main__":
    main()
