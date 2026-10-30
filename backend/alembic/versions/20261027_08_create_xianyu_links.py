"""create xianyu links

Revision ID: 20261027_08
Revises: 20261027_07
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261027_08"
down_revision: str | None = "20261027_07"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "xianyu_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("link", sa.String(2000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_xianyu_links_user_updated", "xianyu_links", ["user_id", "updated_at"])


def downgrade() -> None:
    op.drop_table("xianyu_links")
