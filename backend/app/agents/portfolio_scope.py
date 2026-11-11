"""Carteras de un turno de `/ask` (T4-14): de qué cartera habla cada frase y con qué cifras se
comprueba.

El asistente puede consultar cualquier cartera, pero **cada cartera es independiente**: una frase
solo puede citar cifras de la cartera de la que habla, y nunca se suman cifras de carteras
distintas. Para el guardián, las evidencias van separadas por cartera:

- Una frase que nombra una cartera («la de tus hijos», «Negocio») se comprueba con las cifras de
  esa cartera. Si no nombra ninguna, con las de la última de la que se habló (o la de la pregunta).
- Una frase con cifras que nombra dos carteras se bloquea: un bloque por cartera.
- Una cifra de otra cartera que no se nombra en la frase se bloquea, y el motivo dice de cuál es
  para que el reintento la nombre.

`shared` son las cifras que no son de ninguna cartera (las que trae el texto de una noticia o de
un evento: "0,25 puntos", "2025").
"""

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

from app.agents import guardian
from app.agents import guardian_figures as figs
from app.schemas.agents import Evidence
from app.schemas.portfolio import PortfolioSummaryOut

MAX_TARGETS = 5
"""Carteras cuyos datos se precargan en un turno; las demás, con herramientas."""

KIND_LABELS = {"personal": "personal", "business": "negocio", "family": "familia", "other": "otra"}
_KIND_WORDS = {
    "personal": ("personal",),
    "business": ("negocio", "negocios", "empresa", "sociedad"),
    "family": ("hijo", "hijos", "hija", "hijas", "familia", "familiar", "ninos"),
}
_ALL = re.compile(r"\b(?:carteras|todas|cada una|ambas|las dos|las tres)\b")


@dataclass(frozen=True)
class PortfolioRef:
    id: str
    name: str
    kind: str | None = None

    @classmethod
    def of(cls, summary: PortfolioSummaryOut) -> "PortfolioRef":
        kind = summary.kind.value if summary.kind is not None else None
        return cls(summary.id, summary.name, kind)


def _word(text: str) -> re.Pattern[str]:
    return re.compile(rf"(?<!\w){re.escape(guardian.normalize(text).strip())}(?!\w)")


def mentioned(text: str, refs: Sequence[PortfolioRef]) -> list[str]:
    """Carteras nombradas en el texto, en el orden en que aparecen: por su nombre o, si solo hay
    una de ese tipo, por una palabra del tipo («la de mis hijos» → la cartera `family`)."""
    normalized = guardian.normalize(text)
    found: dict[str, int] = {}
    for ref in refs:
        if not ref.name.strip():
            continue
        match = _word(ref.name).search(normalized)
        if match is not None:
            found[ref.id] = match.start()
    for kind, words in _KIND_WORDS.items():
        of_kind = [ref for ref in refs if ref.kind == kind]
        if len(of_kind) != 1 or of_kind[0].id in found:
            continue
        hits = [m.start() for w in words if (m := _word(w).search(normalized)) is not None]
        if hits:
            found[of_kind[0].id] = min(hits)
    return sorted(found, key=lambda pid: found[pid])


def asks_for_all(question: str) -> bool:
    """«¿Cómo van mis carteras?», «¿y todas?»: la pregunta es por todas las carteras."""
    return _ALL.search(guardian.normalize(question)) is not None


def targets(question: str, refs: Sequence[PortfolioRef], focus: str | None) -> list[str]:
    """Carteras por las que pregunta: las que nombra; todas si pregunta por todas; si no, la
    elegida en la app o, si solo hay una cartera, esa. Vacía si es ambigua."""
    named = mentioned(question, refs)
    if named:
        return named[:MAX_TARGETS]
    if asks_for_all(question) and len(refs) > 1:
        return [ref.id for ref in refs][:MAX_TARGETS]
    if focus is not None:
        return [focus]
    return [refs[0].id] if len(refs) == 1 else []


@dataclass
class Scope:
    """Evidencias del turno separadas por cartera y la cartera de la que se está hablando."""

    refs: list[PortfolioRef]
    subject: str | None = None
    evidence: dict[str, list[Evidence]] = field(default_factory=dict)
    shared: list[Evidence] = field(default_factory=list)

    def name(self, portfolio_id: str) -> str:
        return next((ref.name for ref in self.refs if ref.id == portfolio_id), portfolio_id)

    def add(self, portfolio_id: str | None, items: Iterable[Evidence]) -> None:
        if portfolio_id is None:
            self.shared.extend(items)
        else:
            self.evidence.setdefault(portfolio_id, []).extend(items)

    def attribute(self, text: str) -> list[str]:
        """Carteras de las que habla la frase."""
        named = mentioned(text, self.refs)
        if named:
            return named
        return [self.subject] if self.subject is not None else []

    def evidence_for(self, portfolio_ids: Iterable[str]) -> list[Evidence]:
        out = list(self.shared)
        for portfolio_id in portfolio_ids:
            out.extend(self.evidence.get(portfolio_id, []))
        return out

    def accept(self, portfolio_ids: list[str]) -> None:
        if portfolio_ids:
            self.subject = portfolio_ids[-1]

    def check_mix(self, text: str, portfolio_ids: list[str]) -> str | None:
        """Motivo de bloqueo si la frase mezcla cifras de varias carteras."""
        if len(portfolio_ids) > 1 and guardian.extract_figures(guardian.normalize(text)):
            names = " y ".join(f"«{self.name(pid)}»" for pid in portfolio_ids)
            return (
                f"da cifras de varias carteras a la vez ({names}); cada cartera es independiente: "
                "una frase por cartera y nunca sumes sus cifras"
            )
        return None

    def owner_hint(self, text: str, portfolio_ids: list[str]) -> str | None:
        """Si una cifra que no casa es de otra cartera, de cuál: el reintento debe nombrarla."""
        allowed = self.evidence_for(portfolio_ids)
        for figure in guardian.extract_figures(guardian.normalize(text)):
            if figs.best_match(figure, allowed) is not None:
                continue
            for other, items in self.evidence.items():
                if other not in portfolio_ids and figs.best_match(figure, items) is not None:
                    return (
                        f"esa cifra es de la cartera «{self.name(other)}»: nombra la cartera en "
                        "la frase y usa solo sus cifras"
                    )
        if not portfolio_ids:
            return "no se sabe de qué cartera habla: nombra la cartera en la frase"
        return None
