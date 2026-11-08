"""Esquema inicial: todas las tablas de `SPEC.md` §6 más DCA, ajustes de demo y trazas (T1-01).

Revision ID: 0001
Revises:
Create Date: 2026-11-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agent", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("prompt_hash", sa.String(length=64), nullable=False),
        sa.Column("tool_calls", sa.JSON(), nullable=False),
        sa.Column("output", sa.Text(), nullable=False),
        sa.Column("guardian_verdict", sa.JSON(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("agent_log", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_agent_log_agent"), ["agent"], unique=False)

    op.create_table(
        "asset",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("isin", sa.String(length=12), nullable=True),
        sa.Column("ticker", sa.String(length=20), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("asset_type", sa.String(length=16), nullable=False),
        sa.Column("asset_class", sa.String(length=16), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("ter", sa.Numeric(precision=10, scale=8), nullable=True),
        sa.Column("transferable", sa.Boolean(), nullable=False),
        sa.Column("price_kind", sa.String(length=16), nullable=False),
        sa.Column("price_source", sa.String(length=80), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("isin"),
    )
    with op.batch_alter_table("asset", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_asset_ticker"), ["ticker"], unique=False)

    op.create_table(
        "calc_trace",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("formula", sa.Text(), nullable=False),
        sa.Column("inputs", sa.JSON(), nullable=False),
        sa.Column("outputs", sa.JSON(), nullable=False),
        sa.Column("sources", sa.JSON(), nullable=False),
        sa.Column("parent_calc_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("calc_trace", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_calc_trace_kind"), ["kind"], unique=False)

    op.create_table(
        "event",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("replay", sa.Boolean(), nullable=False),
        sa.Column("source_urls", sa.JSON(), nullable=False),
        sa.Column("entities", sa.JSON(), nullable=False),
        sa.Column("analysis", sa.JSON(), nullable=True),
        sa.Column("analyzed_model", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("event", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_event_occurred_at"), ["occurred_at"], unique=False)

    op.create_table(
        "fx_rate",
        sa.Column("pair", sa.String(length=6), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rate", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.PrimaryKeyConstraint("pair", "ts"),
    )
    op.create_table(
        "portfolio",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("profile", sa.String(length=16), nullable=False),
        sa.Column("base_currency", sa.String(length=3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "alert",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("portfolio_id", sa.String(length=40), nullable=False),
        sa.Column("event_id", sa.String(length=64), nullable=True),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("score", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["event.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolio.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("alert", schema=None) as batch_op:
        batch_op.create_index(
            "ix_alert_portfolio_created", ["portfolio_id", "created_at"], unique=False
        )

    op.create_table(
        "composition",
        sa.Column("fund_asset_id", sa.String(length=40), nullable=False),
        sa.Column("constituent_key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("weight", sa.Numeric(precision=10, scale=8), nullable=False),
        sa.Column("country", sa.String(length=64), nullable=True),
        sa.Column("sector", sa.String(length=64), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("as_of", sa.Date(), nullable=False),
        sa.Column("source", sa.String(length=300), nullable=False),
        sa.ForeignKeyConstraint(["fund_asset_id"], ["asset.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("fund_asset_id", "constituent_key"),
    )
    op.create_table(
        "dca_plan",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("portfolio_id", sa.String(length=40), nullable=False),
        sa.Column("amount_eur", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("frequency", sa.String(length=16), nullable=False),
        sa.Column("day", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("last_execution_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_execution_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolio.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("dca_plan", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_dca_plan_portfolio_id"), ["portfolio_id"], unique=False
        )

    op.create_table(
        "demo_adjustment",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("portfolio_id", sa.String(length=40), nullable=False),
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("asset_id", sa.String(length=40), nullable=False),
        sa.Column("impact_eur", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("label", sa.String(length=80), nullable=False),
        sa.Column("calc_id", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["asset.id"],
        ),
        sa.ForeignKeyConstraint(["event_id"], ["event.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolio.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("demo_adjustment", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_demo_adjustment_portfolio_id"), ["portfolio_id"], unique=False
        )

    op.create_table(
        "event_impact",
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("portfolio_id", sa.String(length=40), nullable=False),
        sa.Column("impact_eur", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("low_eur", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("high_eur", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("impact_pct", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("confidence", sa.String(length=8), nullable=False),
        sa.Column("polarity", sa.String(length=16), nullable=False),
        sa.Column("breakdown", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("explanation_status", sa.String(length=16), nullable=False),
        sa.Column("calc_id", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["event.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolio.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("event_id", "portfolio_id"),
    )
    op.create_table(
        "factor_beta",
        sa.Column("asset_id", sa.String(length=40), nullable=False),
        sa.Column("factor", sa.String(length=16), nullable=False),
        sa.Column("beta", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("std_err", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("r2", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("n_obs", sa.Integer(), nullable=False),
        sa.Column("window_start", sa.Date(), nullable=False),
        sa.Column("window_end", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["asset.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("asset_id", "factor"),
    )
    op.create_table(
        "plan",
        sa.Column("portfolio_id", sa.String(length=40), nullable=False),
        sa.Column("target_equity_pct", sa.Numeric(precision=10, scale=8), nullable=False),
        sa.Column("target_fixed_income_pct", sa.Numeric(precision=10, scale=8), nullable=False),
        sa.Column("target_cash_pct", sa.Numeric(precision=10, scale=8), nullable=False),
        sa.Column("drift_threshold", sa.Numeric(precision=10, scale=8), nullable=False),
        sa.Column("goal_amount_eur", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("goal_year", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolio.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("portfolio_id"),
    )
    op.create_table(
        "price",
        sa.Column("asset_id", sa.String(length=40), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["asset.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("asset_id", "ts"),
    )
    op.create_table(
        "dca_allocation",
        sa.Column("dca_plan_id", sa.String(length=40), nullable=False),
        sa.Column("asset_id", sa.String(length=40), nullable=False),
        sa.Column("weight", sa.Numeric(precision=10, scale=8), nullable=False),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["asset.id"],
        ),
        sa.ForeignKeyConstraint(["dca_plan_id"], ["dca_plan.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("dca_plan_id", "asset_id"),
    )
    op.create_table(
        "dca_execution",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("dca_plan_id", sa.String(length=40), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["dca_plan_id"], ["dca_plan.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("dca_execution", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_dca_execution_dca_plan_id"), ["dca_plan_id"], unique=False
        )

    op.create_table(
        "transaction",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("portfolio_id", sa.String(length=40), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("asset_id", sa.String(length=40), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("units", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("price", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("price_currency", sa.String(length=3), nullable=False),
        sa.Column("fx_rate", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("amount_eur", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("realized_gain_eur", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("linked_tx_id", sa.String(length=40), nullable=True),
        sa.Column("dca_plan_id", sa.String(length=40), nullable=True),
        sa.Column("calc_id", sa.String(length=40), nullable=True),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["asset.id"],
        ),
        sa.ForeignKeyConstraint(
            ["dca_plan_id"],
            ["dca_plan.id"],
        ),
        sa.ForeignKeyConstraint(
            ["linked_tx_id"],
            ["transaction.id"],
        ),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolio.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("transaction", schema=None) as batch_op:
        batch_op.create_index("ix_transaction_portfolio_ts", ["portfolio_id", "ts"], unique=False)

    op.create_table(
        "dca_execution_line",
        sa.Column("execution_id", sa.String(length=40), nullable=False),
        sa.Column("asset_id", sa.String(length=40), nullable=False),
        sa.Column("amount_eur", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("price", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("price_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("units_estimated", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("transaction_id", sa.String(length=40), nullable=True),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["asset.id"],
        ),
        sa.ForeignKeyConstraint(["execution_id"], ["dca_execution.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["transaction_id"],
            ["transaction.id"],
        ),
        sa.PrimaryKeyConstraint("execution_id", "asset_id"),
    )
    op.create_table(
        "tax_lot",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("portfolio_id", sa.String(length=40), nullable=False),
        sa.Column("asset_id", sa.String(length=40), nullable=False),
        sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("units_initial", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("units_remaining", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("cost_eur_per_unit", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("origin_tx_id", sa.String(length=40), nullable=True),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["asset.id"],
        ),
        sa.ForeignKeyConstraint(
            ["origin_tx_id"],
            ["transaction.id"],
        ),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolio.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("tax_lot", schema=None) as batch_op:
        batch_op.create_index(
            "ix_tax_lot_fifo", ["portfolio_id", "asset_id", "acquired_at"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("tax_lot", schema=None) as batch_op:
        batch_op.drop_index("ix_tax_lot_fifo")

    op.drop_table("tax_lot")
    op.drop_table("dca_execution_line")
    with op.batch_alter_table("transaction", schema=None) as batch_op:
        batch_op.drop_index("ix_transaction_portfolio_ts")

    op.drop_table("transaction")
    with op.batch_alter_table("dca_execution", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_dca_execution_dca_plan_id"))

    op.drop_table("dca_execution")
    op.drop_table("dca_allocation")
    op.drop_table("price")
    op.drop_table("plan")
    op.drop_table("factor_beta")
    op.drop_table("event_impact")
    with op.batch_alter_table("demo_adjustment", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_demo_adjustment_portfolio_id"))

    op.drop_table("demo_adjustment")
    with op.batch_alter_table("dca_plan", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_dca_plan_portfolio_id"))

    op.drop_table("dca_plan")
    op.drop_table("composition")
    with op.batch_alter_table("alert", schema=None) as batch_op:
        batch_op.drop_index("ix_alert_portfolio_created")

    op.drop_table("alert")
    op.drop_table("portfolio")
    op.drop_table("fx_rate")
    with op.batch_alter_table("event", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_event_occurred_at"))

    op.drop_table("event")
    with op.batch_alter_table("calc_trace", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_calc_trace_kind"))

    op.drop_table("calc_trace")
    with op.batch_alter_table("asset", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_asset_ticker"))

    op.drop_table("asset")
    with op.batch_alter_table("agent_log", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_agent_log_agent"))

    op.drop_table("agent_log")
