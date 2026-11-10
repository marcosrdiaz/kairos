"""`portfolio.kind` y `portfolio.risk_profile`: carteras creadas por el usuario (T4-10).

Las carteras que ya existen se quedan como `personal` y con el perfil de riesgo que corresponde a
su `profile` (`dinamico` → `agresivo`).

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("portfolio", schema=None) as batch_op:
        batch_op.add_column(sa.Column("kind", sa.String(length=16), nullable=True))
        batch_op.add_column(sa.Column("risk_profile", sa.String(length=16), nullable=True))
    op.execute(
        "UPDATE portfolio SET kind = 'personal', risk_profile = CASE profile "
        "WHEN 'dinamico' THEN 'agresivo' ELSE profile END"
    )


def downgrade() -> None:
    with op.batch_alter_table("portfolio", schema=None) as batch_op:
        batch_op.drop_column("risk_profile")
        batch_op.drop_column("kind")
