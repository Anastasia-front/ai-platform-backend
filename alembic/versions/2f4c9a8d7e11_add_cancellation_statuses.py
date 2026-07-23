"""add cancellation statuses

Revision ID: 2f4c9a8d7e11
Revises: f56bbcc4b15e
Create Date: 2026-07-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "2f4c9a8d7e11"
down_revision: Union[str, Sequence[str], None] = "f56bbcc4b15e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE documentstatus ADD VALUE IF NOT EXISTS 'cancelling'")
    op.execute("ALTER TYPE documentstatus ADD VALUE IF NOT EXISTS 'cancelled'")
    op.execute("ALTER TYPE embeddingstatus ADD VALUE IF NOT EXISTS 'cancelling'")
    op.execute("ALTER TYPE embeddingstatus ADD VALUE IF NOT EXISTS 'cancelled'")


def downgrade() -> None:
    # PostgreSQL cannot drop enum values without recreating the type.
    pass
