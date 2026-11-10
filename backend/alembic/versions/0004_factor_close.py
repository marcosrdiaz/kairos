"""`factor_close`: cierres diarios de los 5 factores en directo, con fecha y fuente (T4-01).

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "factor_close",
        sa.Column("factor", sa.String(length=16), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("value", sa.Numeric(precision=24, scale=12), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("factor", "day"),
    )


def downgrade() -> None:
    op.drop_table("factor_close")
