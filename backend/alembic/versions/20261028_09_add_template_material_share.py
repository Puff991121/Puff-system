"""add template material share

Revision ID: 20261028_09
Revises: 20261027_08
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261028_09"
down_revision: str | None = "20261027_08"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("templates", sa.Column("material_share", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("templates", "material_share")
