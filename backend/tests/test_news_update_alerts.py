"""Avisos tras cada pasada de noticias (TB-02): sin que nadie abra la app.

La pasada es falsa (búsqueda y clasificación sustituidas) y las noticias con su estimación
también (`news_service.list_for_portfolio`), con las cifras trazadas: aquí se prueba que la pasada
lanza la regla de aviso de T4-31, no la regla ni la estimación.
"""

import importlib.util
import sys
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.agents import claude
from app.alerts import repository as alerts_repository
from app.alerts import service as alerts_service
from app.core import clock, trace
from app.main import API_PREFIX
from app.news import service as news_service
from app.news.ingest.runner import NewsIngestReport, SourceSchedule
from app.schemas.alerts import AlertKind
from app.schemas.common import Confidence, Polarity, SourceKind, SourceRef
from app.schemas.events import Relevance
from app.schemas.news import (
    NewsCategory,
    NewsEstimateMethod,
    NewsEstimateOut,
    NewsEstimateStatus,
    NewsItemOut,
)

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "news_update.py"
NOW = datetime(2026, 11, 6, 18, 0, tzinfo=UTC)  # último cierre de `data/prices`
PORTFOLIOS = ("laura", "javier")


@pytest.fixture(scope="module")
def news_update() -> ModuleType:
    spec = importlib.util.spec_from_file_location("news_update_alerts", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["news_update_alerts"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def _setup() -> Iterator[None]:
    clock.set_now(NOW)
    claude.set_client(None)  # mensaje de plantilla
    alerts_service.reset_news_checks()
    yield
    alerts_service.reset_news_checks()


def _news(news_id: str, low: str, high: str) -> NewsItemOut:
    low_eur, high_eur = Decimal(low), Decimal(high)
    published = NOW - timedelta(hours=1)
    calc_id = trace.record(
        "scenario", "noticia de prueba", {"news_id": news_id}, {"low": low, "high": high}, []
    )
    return NewsItemOut(
        id=news_id,
        category=NewsCategory.EARNINGS,
        title="Nvidia presenta resultados trimestrales",
        summary="Resumen.",
        published_at=published,
        source=SourceRef(kind=SourceKind.EVENT, label="Prueba", ref=news_id, as_of=published),
        companies=[],
        asset_ids=["NVDA"],
        channels=[],
        causal_chain=[],
        relevance=Relevance.HIGH,
        estimate=NewsEstimateOut(
            status=NewsEstimateStatus.ESTIMATED,
            polarity=Polarity.RIESGO,
            impact_eur=(low_eur + high_eur) / 2,
            low_eur=low_eur,
            high_eur=high_eur,
            impact_pct=Decimal("-0.05"),
            low_pct=Decimal("-0.07"),
            high_pct=Decimal("-0.03"),
            horizon_sessions=5,
            confidence=Confidence.MEDIA,
            method=NewsEstimateMethod.VOLATILITY,
            analogs_count=25,
            calc_id=calc_id,
            as_of=NOW,
        ),
    )


class _Pass:
    """Una pasada con `created` noticias nuevas, clasificadas, y estas noticias en la cartera."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.monkeypatch = monkeypatch

    def run(self, news_update: ModuleType, *items: NewsItemOut) -> Any:
        created = [item.id for item in items]

        def refresh(schedules: dict[str, SourceSchedule]) -> NewsIngestReport:
            return NewsIngestReport(created=created, read=len(created))

        def list_for_portfolio(
            portfolio_id: str, category: Any = None, affecting: bool = True, limit: int = 50
        ) -> list[NewsItemOut]:
            return list(items)

        self.monkeypatch.setattr(news_service, "refresh", refresh)
        self.monkeypatch.setattr(news_service, "classify_pending", lambda: len(created))
        self.monkeypatch.setattr(news_service, "list_for_portfolio", list_for_portfolio)
        return news_update.poll_once({})


def _news_alerts(portfolio_id: str) -> list[alerts_repository.StoredAlert]:
    return [
        a for a in alerts_repository.list_for(portfolio_id) if a.kind is AlertKind.NEWS_ESTIMATE
    ]


def test_a_big_news_alerts_every_portfolio_without_opening_the_app(
    client: TestClient, news_update: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = _Pass(monkeypatch).run(news_update, _news("n1", "-9000", "-6000"))
    assert result.alerts == {"laura": 1, "javier": 1}
    for portfolio_id in PORTFOLIOS:
        [alert] = _news_alerts(portfolio_id)
        assert alert.news_id == "n1" and alert.calc_id is not None


def test_a_second_big_news_the_same_day_does_not_alert_again(
    client: TestClient, news_update: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    passes = _Pass(monkeypatch)
    passes.run(news_update, _news("n1", "-9000", "-6000"))
    clock.set_now(NOW + timedelta(minutes=5))
    again = passes.run(news_update, _news("n2", "-9500", "-6500"))
    assert again.alerts == {"laura": 0, "javier": 0}
    assert all(len(_news_alerts(p)) == 1 for p in PORTFOLIOS)


def test_small_news_or_nothing_classified_do_not_alert(
    client: TestClient, news_update: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    small = _Pass(monkeypatch).run(news_update, _news("n1", "-2", "-1"))
    assert small.alerts == {"laura": 0, "javier": 0}

    monkeypatch.setattr(news_service, "classify_pending", lambda: 0)
    monkeypatch.setattr(
        news_service, "refresh", lambda schedules: NewsIngestReport(created=[], read=0)
    )
    nothing = news_update.poll_once({})
    assert nothing.alerts == {}  # sin noticias clasificadas no se revisa nada
    assert all(_news_alerts(p) == [] for p in PORTFOLIOS)


def test_the_alert_a_pass_creates_reaches_the_api_with_the_news_the_chart_draws(
    client: TestClient, news_update: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Noticia → aviso → `/alerts` → `/news/{id}`: lo que lee la campana y el punto de la gráfica
    de Inicio (TD-06). La gráfica pide la noticia por el `news_id` del aviso, con su cifra
    trazada."""
    item = _news("n1", "-9000", "-6000")
    _Pass(monkeypatch).run(news_update, item)
    monkeypatch.setattr(news_service, "get_for_portfolio", lambda portfolio_id, news_id: item)

    for portfolio_id in PORTFOLIOS:
        alerts = client.get(f"{API_PREFIX}/portfolios/{portfolio_id}/alerts").json()
        [alert] = [a for a in alerts if a["kind"] == "news_estimate"]
        assert alert["news_id"] == "n1" and alert["event_id"] is None

        news = client.get(f"{API_PREFIX}/portfolios/{portfolio_id}/news/{alert['news_id']}").json()
        assert news["id"] == "n1"
        assert news["estimate"]["calc_id"] == alert["calc_id"]
        assert trace.get(alert["calc_id"]) is not None
