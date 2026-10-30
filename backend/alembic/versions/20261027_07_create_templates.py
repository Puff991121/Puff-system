"""create templates

Revision ID: 20261027_07
Revises: 20260908_06
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261027_07"
down_revision: str | None = "20260908_06"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("figma_share", sa.Text(), nullable=True),
        sa.Column("psd_share", sa.Text(), nullable=True),
        sa.Column("xd_share", sa.Text(), nullable=True),
        sa.Column("jsd_share", sa.Text(), nullable=True),
        sa.Column("html_share", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "name", name="uk_templates_user_name"),
    )
    op.create_index("idx_templates_user_updated", "templates", ["user_id", "updated_at"])


def downgrade() -> None:
    op.drop_table("templates")
