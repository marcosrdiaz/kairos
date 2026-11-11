"""Datos de un turno de `/ask` con varias carteras (T4-14).

Decide por qué carteras pregunta el usuario (`portfolio_scope.targets`), precarga su contexto y
prepara las evidencias del guardián por cartera (`Scope`). También da las frases de plantilla
cuando la pregunta es por varias carteras o no se sabe por cuál.

- `focus`: la cartera elegida en la app (`POST /portfolios/{id}/ask`); `None` en `POST /ask`.
- `targets`: las carteras de la pregunta. Si son varias, se responde una a una, sin sumar.
- `main`: el contexto de `focus`, que va en el bloque con caché del prompt (como antes de T4-14).
- `others`: el contexto de las demás carteras de la pregunta, que va en el mensaje del usuario.
"""

import logging
from dataclasses import dataclass, field

from app.agents import context
from app.agents.context import Preloaded
from app.agents.fact_format import text_evidence
from app.agents.portfolio_scope import PortfolioRef, Scope, targets
from app.core.errors import AppError
from app.portfolio import service as portfolio_service

logger = logging.getLogger(__name__)


@dataclass
class TurnData:
    refs: list[PortfolioRef]
    focus: str | None
    targets: list[str]
    main: Preloaded | None
    others: dict[str, Preloaded] = field(default_factory=dict)
    scope: Scope = field(default_factory=lambda: Scope([]))

    @property
    def default_portfolio(self) -> str | None:
        """Cartera de una herramienta llamada sin `portfolio_id`."""
        return self.targets[0] if len(self.targets) == 1 else self.focus

    @property
    def names(self) -> dict[str, str]:
        return {ref.id: ref.name for ref in self.refs}

    def preloaded(self, portfolio_id: str) -> Preloaded | None:
        if portfolio_id == self.focus:
            return self.main
        return self.others.get(portfolio_id)


def _refs(focus: str | None) -> list[PortfolioRef]:
    """Carteras del usuario. Si no se pueden leer y hay una elegida, solo esa: el turno sigue
    respondiendo por ella como antes de T4-14."""
    try:
        return [PortfolioRef.of(item) for item in portfolio_service.list_portfolios()]
    except Exception:
        if focus is None:
            raise
        logger.warning("Explicador: no se pudo leer la lista de carteras", exc_info=True)
        return [PortfolioRef(focus, focus)]


def load(focus: str | None, question: str) -> TurnData:
    """Lanza `AppError` si la cartera elegida es la de la pregunta y no se puede valorar."""
    refs = _refs(focus)
    if focus is not None and all(ref.id != focus for ref in refs):
        refs.append(PortfolioRef(focus, focus))
    asked = targets(question, refs, focus)
    try:
        main = context.get(focus) if focus is not None else None
    except AppError:
        if focus in asked:
            raise
        main = None
    others: dict[str, Preloaded] = {}
    for portfolio_id in asked:
        if portfolio_id == focus:
            continue
        try:
            others[portfolio_id] = context.get(portfolio_id)
        except AppError:
            logger.info("Explicador: sin contexto de la cartera %s", portfolio_id)
    scope = Scope(refs, subject=asked[0] if len(asked) == 1 else None)
    scope.add(None, text_evidence([ref.name for ref in refs], "portfolios"))
    data = TurnData(refs, focus, asked, main, others, scope)
    for portfolio_id in dict.fromkeys([*([focus] if focus else []), *asked]):
        pre = data.preloaded(portfolio_id)
        if pre is not None:
            scope.add(portfolio_id, pre.evidence())
    return data


# --- Plantillas ---


def _list(names: list[str]) -> str:
    quoted = [f"«{name}»" for name in names]
    return quoted[0] if len(quoted) == 1 else ", ".join(quoted[:-1]) + " y " + quoted[-1]


def ambiguous_answer(data: TurnData) -> list[str]:
    """Sin saber por qué cartera pregunta: las nombra y pide que elija. Sin cifras."""
    if not data.refs:
        return ["Todavía no tienes ninguna cartera: crea una y te cuento cómo va."]
    names = _list([ref.name for ref in data.refs])
    return [f"Tienes estas carteras: {names}. Dime por cuál preguntas y te respondo con sus datos."]


def portfolios_answer(data: TurnData) -> list[str]:
    """Una frase por cartera con su patrimonio, cada una por separado (nunca un total)."""
    sentences: list[str] = []
    for portfolio_id in data.targets:
        pre = data.preloaded(portfolio_id)
        total = pre.fact("total") if pre is not None else None
        name = data.scope.name(portfolio_id)
        if total is None:
            sentences.append(f"De la cartera «{name}» no tengo datos ahora mismo.")
        else:
            sentences.append(f"La cartera «{name}» vale {total.display}.")
    return sentences
