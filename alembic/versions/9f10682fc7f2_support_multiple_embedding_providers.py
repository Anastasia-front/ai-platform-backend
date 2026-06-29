"""support multiple embedding providers

Revision ID: 9f10682fc7f2
Revises: f56bbcc4b15e
Create Date: 2026-06-29 14:03:19.958301

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9f10682fc7f2'
down_revision: Union[str, Sequence[str], None] = 'f56bbcc4b15e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chunk_embeddings",
        sa.Column("provider", sa.String(length=50), nullable=True),
    )

    op.add_column(
        "chunk_embeddings",
        sa.Column("dimensions", sa.Integer(), nullable=True),
    )

    op.execute(
        "UPDATE chunk_embeddings SET provider = 'ollama' WHERE provider IS NULL"
    )

    op.execute(
        "UPDATE chunk_embeddings SET dimensions = 768 WHERE dimensions IS NULL"
    )

    op.alter_column(
        "chunk_embeddings",
        "provider",
        nullable=False,
    )

    op.alter_column(
        "chunk_embeddings",
        "dimensions",
        nullable=False,
    )

    op.drop_constraint(
        op.f("chunk_embeddings_chunk_id_key"),
        "chunk_embeddings",
        type_="unique",
    )

    op.create_index(
        op.f("ix_chunk_embeddings_chunk_id"),
        "chunk_embeddings",
        ["chunk_id"],
        unique=False,
    )

    op.create_unique_constraint(
        "uq_chunk_embedding_provider_model",
        "chunk_embeddings",
        ["chunk_id", "provider", "model_name"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_chunk_embedding_provider_model",
        "chunk_embeddings",
        type_="unique",
    )

    op.drop_index(
        op.f("ix_chunk_embeddings_chunk_id"),
        table_name="chunk_embeddings",
    )

    op.create_unique_constraint(
        op.f("chunk_embeddings_chunk_id_key"),
        "chunk_embeddings",
        ["chunk_id"],
        postgresql_nulls_not_distinct=False,
    )

    op.drop_column("chunk_embeddings", "dimensions")
    op.drop_column("chunk_embeddings", "provider")
