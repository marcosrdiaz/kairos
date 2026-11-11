"""`alert.news_id`: la noticia de un aviso `news_estimate` (T4-31).

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("alert", schema=None) as batch_op:
        batch_op.add_column(sa.Column("news_id", sa.String(length=32), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("alert", schema=None) as batch_op:
        batch_op.drop_column("news_id")
