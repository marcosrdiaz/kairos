"""`pending_event` (eventos pendientes de cierre, sin shock medido todavía) y `event.payload`
(el `EventIn` completo de los eventos reales) (T4-04).

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("event", schema=None) as batch_op:
        batch_op.add_column(sa.Column("payload", sa.JSON(), nullable=True))
    op.create_table(
        "pending_event",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("companies", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["id"], ["event.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("pending_event")
    with op.batch_alter_table("event", schema=None) as batch_op:
        batch_op.drop_column("payload")
