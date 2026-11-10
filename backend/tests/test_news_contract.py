"""Contrato de noticias (T4-27): reglas del esquema y rutas provisionales sobre los ejemplos.

Los ejemplos se validan también en `test_schema_examples.py`.
"""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import API_PREFIX
from app.schemas import examples
from app.schemas.alerts import AlertKind, AlertOut
from app.schemas.news import NewsChannel, NewsEstimateOut, NewsItemOut

URL = f"{API_PREFIX}/portfolios/laura/news"


def _estimate(**changes: Any) -> dict[str, Any]:
    data: dict[str, Any] = examples.load("NewsItemOut")["estimate"]
    data.update(changes)
    return data


# --- Esquema ---


def test_estimated_needs_all_its_figures() -> None:
    with pytest.raises(ValidationError, match="todas sus cifras"):
        NewsEstimateOut.model_validate(_estimate(calc_id=None))


def test_estimate_range_must_contain_the_central_value() -> None:
    with pytest.raises(ValidationError, match="Rango incoherente"):
        NewsEstimateOut.model_validate(_estimate(low_eur="-100.00"))


@pytest.mark.parametrize("status", ["pending", "not_relevant"])
def test_pending_and_not_relevant_carry_no_figures(status: str) -> None:
    with pytest.raises(ValidationError, match="no lleva cifras"):
        NewsEstimateOut.model_validate(_estimate(status=status))


def test_classification_texts_have_no_digits() -> None:
    """Regla 1: el agente clasificador no pone cifras."""
    item = examples.load("NewsItemOut")
    item["causal_chain"] = ["La acción puede caer un 5 %."]
    with pytest.raises(ValidationError, match="regla 1"):
        NewsItemOut.model_validate(item)
    with pytest.raises(ValidationError, match="regla 1"):
        NewsChannel.model_validate(
            {"factor": "OIL", "direction": "up", "label": "petróleo", "rationale": "Sube 3 %."}
        )


def test_channel_is_a_factor_or_a_company() -> None:
    texts = {"direction": "up", "label": "x", "rationale": "y"}
    with pytest.raises(ValidationError, match="no de los dos"):
        NewsChannel.model_validate({"factor": "OIL", "company_key": "NVDA", **texts})
    with pytest.raises(ValidationError, match="no de los dos"):
        NewsChannel.model_validate(texts)


def test_alerts_have_a_news_kind_and_an_optional_news_id() -> None:
    old = examples.load("AlertOut")
    del old["news_id"]
    assert AlertOut.model_validate(old).news_id is None
    alert = AlertOut.model_validate(examples.load("AlertOut.news_estimate"))
    assert alert.kind is AlertKind.NEWS_ESTIMATE and alert.news_id


# --- Rutas provisionales ---


def test_provisional_routes_never_serve_the_examples(client: TestClient) -> None:
    """Sin ingesta (T4-28) no hay noticias: nada de datos de ejemplo en la app."""
    response = client.get(URL, params={"affecting": "false"})
    assert response.status_code == 200, response.text
    assert response.json() == []
    news_id = examples.load("NewsItemOut")["id"]
    assert client.get(f"{URL}/{news_id}").status_code == 404


def test_routes_check_the_portfolio_and_the_filters(client: TestClient) -> None:
    assert client.get(f"{API_PREFIX}/portfolios/missing/news").status_code == 404
    assert client.get(URL, params={"category": "sports"}).status_code == 422
