"""Noticias en producción cada pocos minutos (TB-01 y TB-02): busca, clasifica y avisa.

Cada pasada:
1. Busca lo nuevo en las fuentes a las que les toca (`news.service.refresh`): los RSS de Yahoo
   Finance y de la Reserva Federal cada `NEWS_POLL_MINUTES` y Google Noticias cada
   `NEWS_GOOGLE_MINUTES`. Si una fuente nos limita, espera más; las demás siguen.
2. Clasifica con Claude lo que aún no lo esté (`classify_pending`). Sin `ANTHROPIC_API_KEY` las
   guarda sin clasificar y lo registra: no salen en «Te afectan» hasta que se clasifiquen.
3. Si ha clasificado alguna, revisa los avisos por noticia de cada cartera
   (`alerts.service.check_news`) con la regla de siempre (T4-31): sin esperar a que alguien abra
   la app.

Solo en producción (`DEMO_MODE=false`); en modo demo no hace nada y termina, para que la demo no
cambie. Un error de una pasada se registra y no para el proceso.

    python /scripts/news_update.py --loop      # servicio `news-updater` de Compose
    cd backend && uv run python ../scripts/news_update.py --once
"""

from __future__ import annotations

import argparse
import logging
import sys
import time as time_module
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING

# En Docker el código está en /app (directorio de trabajo); en local, en <repo>/backend.
for candidate in (Path.cwd(), Path(__file__).resolve().parents[1] / "backend"):
    if (candidate / "app" / "__init__.py").is_file() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))
        break

if TYPE_CHECKING:
    from app.news.ingest.runner import NewsIngestReport, SourceSchedule

log = logging.getLogger("news_update")


@dataclass
class PassResult:
    report: NewsIngestReport | None = None
    classified: int = 0
    alerts: dict[str, int] = field(default_factory=dict)
    """Cartera → avisos creados o rehechos en esta pasada."""
    skipped: bool = False
    """Había otra pasada en curso."""


def schedules() -> dict[str, SourceSchedule]:
    from app.config import get_settings
    from app.news import service as news_service

    settings = get_settings()
    return {
        "google": news_service.SourceSchedule(timedelta(minutes=settings.news_google_minutes)),
        "rss": news_service.SourceSchedule(timedelta(minutes=settings.news_poll_minutes)),
    }


def _check_alerts() -> dict[str, int]:
    """TB-02: la misma revisión que al leer los avisos, ya (umbral según el perfil, un aviso por
    cartera y día, cupo semanal). `force` solo se salta la espera entre revisiones del backend."""
    from app.alerts import service as alerts_service
    from app.portfolio import service as portfolio_service

    alerts: dict[str, int] = {}
    for portfolio_id in portfolio_service.list_portfolio_ids():
        try:
            alerts[portfolio_id] = alerts_service.check_news(portfolio_id, force=True)
        except Exception:
            log.exception("Avisos por noticia de %s: error; se reintenta luego", portfolio_id)
    return alerts


def poll_once(sources: dict[str, SourceSchedule]) -> PassResult:
    from app.news import service as news_service

    report = news_service.refresh(sources)
    if report is None:
        log.info("Noticias: la pasada anterior sigue en curso; se salta esta")
        return PassResult(skipped=True)
    result = PassResult(report=report, classified=news_service.classify_pending())
    if result.classified:
        result.alerts = _check_alerts()
    log.info(
        "Noticias: %d leídas, %d nuevas, %d clasificadas, %d avisos, %d fallos%s",
        report.read,
        len(report.created),
        result.classified,
        sum(result.alerts.values()),
        len(report.failed),
        f" (limitadas: {', '.join(sorted(report.limited))})" if report.limited else "",
    )
    for name, reason in sorted(report.failed.items()):
        log.debug("  %s: %s", name, reason)
    return result


def safe_poll(sources: dict[str, SourceSchedule]) -> PassResult | None:
    try:
        return poll_once(sources)
    except Exception:
        log.exception("Noticias: error inesperado; se reintenta en la próxima pasada")
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--once", action="store_true", help="una pasada y termina")
    mode.add_argument("--loop", action="store_true", help="una pasada cada NEWS_POLL_MINUTES")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    from app.config import get_settings

    settings = get_settings()
    if settings.demo_mode:
        log.info("Modo demo: las noticias salen de data/news; no se busca nada")
        return 0
    sources = schedules()
    if args.once:
        safe_poll(sources)
        return 0
    every = settings.news_poll_minutes * 60
    log.info(
        "Noticias cada %d min (Google Noticias cada %d min)",
        settings.news_poll_minutes,
        settings.news_google_minutes,
    )
    while True:
        started = time_module.monotonic()
        safe_poll(sources)
        time_module.sleep(max(0.0, every - (time_module.monotonic() - started)))


if __name__ == "__main__":
    sys.exit(main())
