"""Carga de `data/seed` (formato en D-038): catálogo y carteras de ejemplo (TD-09).

Carmen (ID `laura`, moderada), Javier (conservador) y Víctor (agresivo, cartera familiar).

Solo lo llama `portfolio/service.py` (`load_seed`, `reset_demo`).
"""

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core import clock
from app.core.db import session_scope
from app.portfolio import ledger, manage, repository
from app.schemas.common import PortfolioKind, Profile, RiskProfile

SEED_DIR = Path(__file__).resolve().parents[3] / "data" / "seed"
"""En local, `<repo>/data/seed`; en Docker, `/data/seed` (montado en Compose)."""
SEED_PORTFOLIOS = ("laura", "javier", "victor")
"""`laura` se muestra como «Carmen» (TD-09): el ID no cambia para no tocar tests ni contratos."""


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load(force: bool = False, seed_dir: Path = SEED_DIR, portfolios: bool = True) -> list[str]:
    """Idempotente: el catálogo se actualiza siempre; cada cartera se crea si no existe y, con
    `force`, vuelve a su estado inicial (plan, DCA y lotes). Devuelve los IDs del seed cargados.

    Con `portfolios=False` solo carga el catálogo (T4-10): la app arranca sin carteras."""
    now = clock.now()
    with session_scope() as session:
        repository.upsert_assets(session, _read_json(seed_dir / "assets.json")["assets"])
        if not portfolios:
            return []
        for pid in SEED_PORTFOLIOS:
            if repository.get_portfolio(session, pid) is not None and not force:
                continue
            _load_portfolio(session, _read_json(seed_dir / "portfolios" / f"{pid}.json"), now)
    return list(SEED_PORTFOLIOS)


def _load_portfolio(session: Session, raw: dict[str, Any], now: datetime) -> None:
    pid = str(raw["id"])
    profile = Profile(raw["profile"])
    risk = RiskProfile(raw["risk_profile"]) if "risk_profile" in raw else None
    repository.upsert_portfolio(
        session,
        pid,
        raw["name"],
        profile.value,
        raw["base_currency"],
        now,
        kind=PortfolioKind(raw.get("kind", PortfolioKind.PERSONAL.value)).value,
        risk_profile=(risk or manage.risk_from_profile(profile)).value,
    )
    repository.clear_portfolio(session, pid)
    repository.set_plan(session, pid, raw["plan"])
    for dca in raw.get("dca_plans", []):
        repository.add_dca_plan(session, pid, dca)
    for position in raw["positions"]:
        for lot in position["lots"]:
            ledger.add_initial_lot(
                session,
                pid,
                position["asset_id"],
                datetime.fromisoformat(lot["acquired_at"]),
                Decimal(lot["units"]),
                Decimal(lot["cost_eur_per_unit"]),
            )
