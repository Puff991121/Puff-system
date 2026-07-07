"""create asset accounts table

Revision ID: 20260706_03
Revises: 20260703_02
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260706_03"
down_revision: str | None = "20260703_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "asset_accounts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("account", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "type", "account", name="uk_asset_account_user_type_name"),
    )
    op.create_index(
        "idx_asset_accounts_user_type_sort",
        "asset_accounts",
        ["user_id", "type", "sort_order"],
    )


def downgrade() -> None:
    op.drop_index("idx_asset_accounts_user_type_sort", table_name="asset_accounts")
    op.drop_table("asset_accounts")
