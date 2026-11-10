"""`python -m app.events.ingest`: una pasada de la ingesta de noticias (T4-05)."""

import logging
import sys

from app.events.ingest.runner import run_once


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    report = run_once()
    print(f"Nuevos: {len(report.created)} · ya vistos: {len(report.skipped)}")
    for source, reason in report.failed.items():
        print(f"Fallo: {source}: {reason}")
    return 1 if report.failed else 0


if __name__ == "__main__":
    sys.exit(main())
