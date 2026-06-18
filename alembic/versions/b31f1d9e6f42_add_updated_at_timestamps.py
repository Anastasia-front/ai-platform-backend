"""add updated_at timestamps

Revision ID: b31f1d9e6f42
Revises: 91cc967ec6f2
Create Date: 2026-06-18 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "b31f1d9e6f42"
down_revision: Union[str, Sequence[str], None] = "91cc967ec6f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLES = (
    "users",
    "projects",
    "chats",
    "messages",
    "documents",
    "workflows",
    "agent_runs",
    "workflow_steps",
    "workflow_runs",
    "workflow_step_runs",
    "workflow_run_events",
)


def upgrade() -> None:
    for table_name in TABLES:
        op.alter_column(
            table_name,
            "created_at",
            server_default=sa.text("now()"),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
        )
        op.add_column(
            table_name,
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )


def downgrade() -> None:
    for table_name in reversed(TABLES):
        op.drop_column(table_name, "updated_at")
        op.alter_column(
            table_name,
            "created_at",
            server_default=None,
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
        )
