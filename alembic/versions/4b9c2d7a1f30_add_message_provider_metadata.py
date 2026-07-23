"""add_message_provider_metadata

Revision ID: 4b9c2d7a1f30
Revises: 6ad2f8c9e013
Create Date: 2026-07-14 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "4b9c2d7a1f30"
down_revision: Union[str, Sequence[str], None] = "6ad2f8c9e013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("provider_used", sa.String(length=50), nullable=True))
    op.add_column("messages", sa.Column("model_used", sa.String(length=100), nullable=True))
    op.add_column("messages", sa.Column("fallback_used", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("messages", "fallback_used")
    op.drop_column("messages", "model_used")
    op.drop_column("messages", "provider_used")
