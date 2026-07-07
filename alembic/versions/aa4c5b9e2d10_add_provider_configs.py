"""add provider configs

Revision ID: aa4c5b9e2d10
Revises: 9f10682fc7f2
Create Date: 2026-07-07 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "aa4c5b9e2d10"
down_revision: Union[str, Sequence[str], None] = "9f10682fc7f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "provider_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=255), nullable=False),
        sa.Column("fallback_model", sa.String(length=255), nullable=True),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("encrypted_api_key", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("dimensions", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("kind", "provider", name="uq_provider_configs_kind_provider"),
    )
    op.create_index(op.f("ix_provider_configs_id"), "provider_configs", ["id"], unique=False)
    op.create_index(op.f("ix_provider_configs_kind"), "provider_configs", ["kind"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_provider_configs_kind"), table_name="provider_configs")
    op.drop_index(op.f("ix_provider_configs_id"), table_name="provider_configs")
    op.drop_table("provider_configs")
