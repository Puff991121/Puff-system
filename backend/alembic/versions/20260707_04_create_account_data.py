"""create account data tables

Revision ID: 20260707_04
Revises: 20260706_03
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260707_04"
down_revision: str | None = "20260706_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "account_data_fields",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("field_key", sa.String(50), nullable=False),
        sa.Column("label", sa.String(20), nullable=False),
        sa.Column("field_type", sa.String(20), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "field_key", name="uk_account_field_user_key"),
        sa.UniqueConstraint("user_id", "label", name="uk_account_field_user_label"),
    )
    op.create_index(
        "idx_account_fields_user_sort", "account_data_fields", ["user_id", "sort_order"]
    )
    op.create_table(
        "account_data_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("values_json", sa.JSON(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_account_records_user_sort", "account_data_records", ["user_id", "sort_order"]
    )


def downgrade() -> None:
    op.drop_index("idx_account_records_user_sort", table_name="account_data_records")
    op.drop_table("account_data_records")
    op.drop_index("idx_account_fields_user_sort", table_name="account_data_fields")
    op.drop_table("account_data_fields")
