"""`analysis_cache`: análisis del modelo reutilizables entre replays y resets (T2-26).

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "analysis_cache",
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("key", sa.String(length=40), nullable=False),
        sa.Column("analysis", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("event_id", "key"),
    )


def downgrade() -> None:
    op.drop_table("analysis_cache")
