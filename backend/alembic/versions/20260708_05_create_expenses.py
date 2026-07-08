"""create expenses

Revision ID: 20260708_05
Revises: 20260707_04
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260708_05"
down_revision: str | None = "20260707_04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table("expenses", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("transaction_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("transaction_type", sa.String(30), nullable=False),
        sa.Column("counterparty", sa.String(100), nullable=False),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("payment_method", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("idx_expenses_user_time", "expenses", ["user_id", "transaction_time"])
    op.create_index("idx_expenses_user_type", "expenses", ["user_id", "transaction_type"])
    op.create_index("idx_expenses_user_payment", "expenses", ["user_id", "payment_method"])


def downgrade() -> None:
    op.drop_table("expenses")
