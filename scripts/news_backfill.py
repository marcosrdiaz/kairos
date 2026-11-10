"""Carga la base de noticias reales de un periodo (T4-28, T4-29).

1. Lee las fuentes (Google Noticias; con `--gdelt`, también GDELT; si el periodo acaba hoy o
   ayer, los RSS de Yahoo Finance y de la Reserva Federal) y guarda lo nuevo, sin duplicados.
2. Con `--classify`, clasifica con Claude lo que aún no lo esté (necesita `ANTHROPIC_API_KEY`).
3. Con `--export <fichero>`, escribe las noticias del periodo en `data/news/` (JSON Lines), que
   el servicio `seed` carga en cada `make up` (`--load`).

    cd backend && uv run python ../scripts/news_backfill.py --start 2026-11-01 --end 2026-11-10 \
        --classify --export ../data/news/2026-11.jsonl
    python /scripts/news_backfill.py --load            # servicio `seed` de Compose
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import UTC, date, datetime, time
from pathlib import Path

for candidate in (Path.cwd(), Path(__file__).resolve().parents[1] / "backend"):
    if (candidate / "app" / "__init__.py").is_file() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))
        break

log = logging.getLogger("news_backfill")


def _day(text: str) -> date:
    return date.fromisoformat(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--start", type=_day, help="primer día (AAAA-MM-DD)")
    parser.add_argument("--end", type=_day, help="último día, incluido (AAAA-MM-DD)")
    parser.add_argument("--gdelt", action="store_true", help="buscar también en GDELT")
    parser.add_argument("--no-rss", action="store_true", help="sin RSS de Yahoo y de la Fed")
    parser.add_argument("--classify", action="store_true", help="clasificar con Claude")
    parser.add_argument("--export", type=Path, help="escribir el periodo en este .jsonl")
    parser.add_argument("--load", action="store_true", help="cargar data/news/*.jsonl")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    from app.news import service

    if args.load:
        print(f"news: {service.load_snapshot()} noticias cargadas de {service.NEWS_DIR}")
    start = datetime.combine(args.start, time.min, UTC) if args.start else None
    end = datetime.combine(args.end, time.max, UTC) if args.end else None
    if start is not None and end is not None:
        report = service.ingest(start, end, use_gdelt=args.gdelt, use_rss=not args.no_rss)
        print(f"news: {report.read} leídas, {len(report.created)} nuevas")
        for name, reason in report.failed.items():
            print(f"news: falló {name}: {reason}")
    if args.classify:
        classify = getattr(service, "classify_pending", None)
        if classify is None:
            print("news: esta versión aún no clasifica (T4-29)")
        else:
            print(f"news: {classify()} noticias clasificadas")
    if args.export is not None:
        print(f"news: {service.export_snapshot(args.export, start, end)} noticias en {args.export}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
