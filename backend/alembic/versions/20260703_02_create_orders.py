"""create orders table

Revision ID: 20260703_02
Revises: 20260703_01
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260703_02"
down_revision: str | None = "20260703_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("order_no", sa.String(length=40), nullable=False),
        sa.Column("order_date", sa.Date(), nullable=False),
        sa.Column("requirement", sa.String(length=500), nullable=False),
        sa.Column("template", sa.String(length=100), nullable=False),
        sa.Column("format", sa.String(length=20), nullable=False),
        sa.Column("school", sa.String(length=100), nullable=False),
        sa.Column("price", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("payment_method", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_no"),
    )
    op.create_index("idx_orders_user_date", "orders", ["user_id", "order_date"])
    op.create_index("idx_orders_user_payment", "orders", ["user_id", "payment_method"])


def downgrade() -> None:
    op.drop_index("idx_orders_user_payment", table_name="orders")
    op.drop_index("idx_orders_user_date", table_name="orders")
    op.drop_table("orders")
