"""`news_item`: noticias de fuentes reales y su clasificación (T4-28, T4-29).

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "news_item",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("url", sa.String(length=2000), nullable=False),
        sa.Column("url_key", sa.String(length=64), nullable=False),
        sa.Column("title_key", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_name", sa.String(length=120), nullable=False),
        sa.Column("provider", sa.String(length=16), nullable=False),
        sa.Column("language", sa.String(length=8), nullable=False),
        sa.Column("query", sa.String(length=300), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("classification", sa.JSON(), nullable=True),
        sa.Column("classified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("classifier_key", sa.String(length=40), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url_key"),
    )
    op.create_index("ix_news_item_title_key", "news_item", ["title_key"])
    op.create_index("ix_news_item_published_at", "news_item", ["published_at"])


def downgrade() -> None:
    op.drop_index("ix_news_item_published_at", table_name="news_item")
    op.drop_index("ix_news_item_title_key", table_name="news_item")
    op.drop_table("news_item")
