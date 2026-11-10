"""La migración de Alembic crea exactamente el esquema de los modelos (T1-01).

Si alguien cambia un `models.py` sin añadir migración, `test_migration_matches_models` falla.
"""

from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import inspect

import app.models  # noqa: F401  (registra todas las tablas)
from app.core.db import Base, get_engine

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"

EXPECTED_TABLES = {
    "portfolio",
    "plan",
    "asset",
    "price",
    "fx_rate",
    "factor_close",
    "transaction",
    "tax_lot",
    "dca_plan",
    "dca_allocation",
    "dca_execution",
    "dca_execution_line",
    "demo_adjustment",
    "composition",
    "factor_beta",
    "event",
    "pending_event",
    "event_impact",
    "alert",
    "calc_trace",
    "agent_log",
}


def _config() -> Config:
    cfg = Config(str(ALEMBIC_INI))
    cfg.attributes["configure_logger"] = False  # no tocar el logging de pytest
    return cfg


def test_models_declare_all_spec_tables() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_upgrade_head_creates_all_tables() -> None:
    command.upgrade(_config(), "head")
    tables = set(inspect(get_engine()).get_table_names())
    assert tables == EXPECTED_TABLES | {"alembic_version"}


def test_migration_matches_models() -> None:
    command.upgrade(_config(), "head")
    with get_engine().connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    assert diff == []


def test_downgrade_base_drops_everything() -> None:
    cfg = _config()
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")
    assert set(inspect(get_engine()).get_table_names()) == {"alembic_version"}


def test_models_roundtrip_decimal_and_fk(db: None) -> None:
    """Un lote se guarda y se lee con `Decimal` exacto y sus claves foráneas."""
    from datetime import UTC, datetime
    from decimal import Decimal

    from sqlalchemy import select

    from app.core.db import session_scope
    from app.portfolio.models import Asset, Portfolio, TaxLot

    when = datetime(2023, 3, 6, tzinfo=UTC)
    with session_scope() as s:
        s.add(Portfolio(id="laura", name="Laura", profile="dinamico", created_at=when))
        s.add(
            Asset(
                id="IE00B03HD191",
                isin="IE00B03HD191",
                name="Fondo de prueba",
                asset_type="fund",
                asset_class="equity",
                currency="EUR",
                transferable=True,
                price_kind="nav_daily",
                price_source="fixed:1",
            )
        )
        s.flush()
        s.add(
            TaxLot(
                id="lot_1",
                portfolio_id="laura",
                asset_id="IE00B03HD191",
                acquired_at=when,
                units_initial=Decimal("200.31765635"),
                units_remaining=Decimal("200.31765635"),
                cost_eur_per_unit=Decimal("36.53000000"),
            )
        )

    with session_scope() as s:
        lot = s.scalars(select(TaxLot)).one()
        assert lot.units_remaining == Decimal("200.31765635")
        assert isinstance(lot.cost_eur_per_unit, Decimal)
