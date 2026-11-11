"""Piezas puras del asistente sobre cualquier cartera (T4-14).

De qué cartera habla una frase (`portfolio_scope.py`) y las cifras de noticias, avisos, radar,
agenda y estado (`data_facts.py`).
"""

from decimal import Decimal

from app.agents import data_facts
from app.agents.fact_format import as_evidence, money
from app.agents.portfolio_scope import PortfolioRef, Scope, asks_for_all, mentioned, targets
from app.schemas import examples
from app.schemas.alerts import AlertOut
from app.schemas.news import NewsItemOut
from app.schemas.planning import AgendaItemOut
from app.schemas.radar import RadarOut
from app.schemas.status import StatusOut

REFS = [
    PortfolioRef("pf_p", "Personal", "personal"),
    PortfolioRef("pf_n", "Negocio", "business"),
    PortfolioRef("pf_h", "Ahorro peques", "family"),
]


def test_mentioned_by_name_and_by_kind_word_in_order() -> None:
    assert mentioned("¿Cómo va la de mis hijos?", REFS) == ["pf_h"]
    assert mentioned("Ahorro Peques y NEGOCIO", REFS) == ["pf_h", "pf_n"]
    assert mentioned("La de la empresa frente a la personal", REFS) == ["pf_n", "pf_p"]
    assert mentioned("datos personales", REFS) == []  # palabra entera


def test_kind_word_needs_a_single_portfolio_of_that_kind() -> None:
    two_family = [*REFS, PortfolioRef("pf_h2", "Universidad", "family")]
    assert mentioned("¿Y la de mis hijos?", two_family) == []


def test_targets() -> None:
    assert targets("¿Cómo van mis carteras?", REFS, "pf_p") == ["pf_p", "pf_n", "pf_h"]
    assert targets("¿Cómo va el negocio?", REFS, "pf_p") == ["pf_n"]
    assert targets("¿Cómo va?", REFS, "pf_p") == ["pf_p"]
    assert targets("¿Cómo va?", REFS, None) == []
    assert targets("¿Cómo va?", REFS[:1], None) == ["pf_p"]
    assert asks_for_all("¿y cada una?")


def test_scope_checks_each_sentence_against_its_portfolio() -> None:
    scope = Scope(REFS, subject="pf_p")
    scope.add("pf_p", as_evidence([money("total", "patrimonio", Decimal("1000"), "calc_p")]))
    scope.add("pf_n", as_evidence([money("total", "patrimonio", Decimal("5000"), "calc_n")]))

    assert scope.attribute("Vale 1.000 euros.") == ["pf_p"]
    assert scope.attribute("Negocio vale 5.000 euros.") == ["pf_n"]
    hint = scope.owner_hint("Vale 5.000 euros.", ["pf_p"])
    assert hint is not None and "«Negocio»" in hint
    mix = scope.check_mix("Personal 1.000 euros y Negocio 5.000 euros.", ["pf_p", "pf_n"])
    assert mix is not None and "nunca sumes" in mix
    assert scope.check_mix("Tienes Personal y Negocio.", ["pf_p", "pf_n"]) is None
    scope.accept(["pf_n"])
    assert scope.attribute("Sigue igual.") == ["pf_n"]


def test_news_facts_copy_the_engine_estimate() -> None:
    item = NewsItemOut.model_validate(examples.load("NewsItemOut"))
    found = {f.key: f for f in data_facts.news_facts(item)}
    estimate = item.estimate
    assert estimate is not None and estimate.impact_eur is not None
    impact = found[f"news.{item.id}.impact"]
    assert (impact.value, impact.calc_id) == (estimate.impact_eur, estimate.calc_id)
    assert f"news.{item.id}.low_pct" in found
    for name in ("NewsItemOut.pending", "NewsItemOut.not_relevant"):
        assert data_facts.news_facts(NewsItemOut.model_validate(examples.load(name))) == []


def test_news_text_evidence_has_no_calc_id_and_includes_year() -> None:
    item = NewsItemOut.model_validate(examples.load("NewsItemOut"))
    evidence = data_facts.news_text_evidence(item)
    assert all(e.calc_id is None for e in evidence)
    assert any(e.unit == "year" and e.value == item.published_at.year for e in evidence)


def test_status_alerts_radar_and_agenda() -> None:
    status = StatusOut.model_validate(examples.load("StatusOut"))
    assert data_facts.status_facts(status)[0].value == status.total_eur

    alert = AlertOut.model_validate(examples.load("AlertOut"))
    traced = [e for e in data_facts.alert_evidence([alert]) if e.calc_id]
    assert all(e.calc_id == alert.calc_id for e in traced)

    radar = RadarOut.model_validate(examples.load("RadarOut"))
    assert all(f.calc_id for f in data_facts.radar_facts(radar))

    agenda = [AgendaItemOut.model_validate(examples.load("AgendaItemOut"))]
    facts = data_facts.agenda_facts(agenda)
    assert all(f.calc_id == agenda[0].calc_id for f in facts)
