"""add celery job tracking columns

Revision ID: d1a4c9b7f210
Revises: aa4c5b9e2d10
Create Date: 2026-07-10 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "d1a4c9b7f210"
down_revision: Union[str, Sequence[str], None] = "aa4c5b9e2d10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    embeddingstatus = sa.Enum(
        "pending",
        "queued",
        "processing",
        "completed",
        "failed",
        name="embeddingstatus",
    )

    op.execute("ALTER TYPE documentstatus ADD VALUE IF NOT EXISTS 'queued'")
    op.execute("ALTER TYPE embeddingstatus ADD VALUE IF NOT EXISTS 'queued'")

    op.add_column(
        "documents",
        sa.Column("celery_task_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("processing_error", sa.Text(), nullable=True),
    )

    op.add_column(
        "workflow_runs",
        sa.Column("celery_task_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "workflow_runs",
        sa.Column("error", sa.Text(), nullable=True),
    )

    op.add_column(
        "projects",
        sa.Column(
            "embedding_sync_status",
            embeddingstatus,
            nullable=False,
            server_default="pending",
        ),
    )
    op.add_column(
        "projects",
        sa.Column("embedding_sync_task_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column("embedding_sync_error", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("projects", "embedding_sync_error")
    op.drop_column("projects", "embedding_sync_task_id")
    op.drop_column("projects", "embedding_sync_status")

    op.drop_column("workflow_runs", "error")
    op.drop_column("workflow_runs", "celery_task_id")

    op.drop_column("documents", "processing_error")
    op.drop_column("documents", "celery_task_id")

    # Postgres cannot drop enum values; the added 'queued' labels are left
    # in place on downgrade (harmless, matches existing project convention
    # of not reversing enum-value additions).
