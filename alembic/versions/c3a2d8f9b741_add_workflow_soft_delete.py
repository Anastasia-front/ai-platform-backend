"""add workflow soft delete

Revision ID: c3a2d8f9b741
Revises: 4b9c2d7a1f30
Create Date: 2026-07-14 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "c3a2d8f9b741"
down_revision: Union[str, Sequence[str], None] = "4b9c2d7a1f30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "workflows",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_workflows_deleted_at",
        "workflows",
        ["deleted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_workflows_deleted_at", table_name="workflows")
    op.drop_column("workflows", "deleted_at")
