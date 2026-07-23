"""add_document_embedding_metadata

Revision ID: 6ad2f8c9e013
Revises: 2f4c9a8d7e11, d1a4c9b7f210
Create Date: 2026-07-13 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6ad2f8c9e013"
down_revision: Union[str, Sequence[str], None] = (
    "2f4c9a8d7e11",
    "d1a4c9b7f210",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("embedding_provider", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("embedding_model", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("embedding_dimensions", sa.Integer(), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("embeddings_updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("documents", "embeddings_updated_at")
    op.drop_column("documents", "embedding_dimensions")
    op.drop_column("documents", "embedding_model")
    op.drop_column("documents", "embedding_provider")
