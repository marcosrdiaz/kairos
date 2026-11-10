"""`factor_beta.computed_at`: cuándo se calcularon las betas, para recalcularlas (T4-03).

Nullable: las filas que ya había no tienen fecha y la próxima actualización las sustituye.

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("factor_beta", schema=None) as batch_op:
        batch_op.add_column(sa.Column("computed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("factor_beta", schema=None) as batch_op:
        batch_op.drop_column("computed_at")
