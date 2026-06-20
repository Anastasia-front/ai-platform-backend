"""adjust_statuses_default_values

Revision ID: e20a94017dae
Revises: b2f0618f384e
Create Date: 2026-06-20 02:21:40.417267
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e20a94017dae"
down_revision: Union[str, Sequence[str], None] = "b2f0618f384e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


document_status = postgresql.ENUM(
    "uploaded",
    "processing",
    "indexed",
    "failed",
    name="documentstatus",
)

embedding_status = postgresql.ENUM(
    "PENDING",
    "PROCESSING",
    "COMPLETED",
    "FAILED",
    name="embeddingstatus",
)


def upgrade() -> None:
    # Create enum types
    document_status.create(op.get_bind(), checkfirst=True)
    embedding_status.create(op.get_bind(), checkfirst=True)

    # Convert documents.status
    op.alter_column(
        "documents",
        "status",
        existing_type=sa.String(length=50),
        type_=document_status,
        existing_nullable=False,
        postgresql_using="status::documentstatus",
    )

    # Convert documents.embedding_status
    # op.alter_column(
    #     "documents",
    #     "embedding_status",
    #     existing_type=sa.String(length=20),
    #     type_=embedding_status,
    #     existing_nullable=False,
    #     existing_server_default=sa.text("'PENDING'::character varying"),
    #     postgresql_using="embedding_status::embeddingstatus",
    # )

    op.alter_column(
        "workflow_steps",
        "depends_on",
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "workflow_steps",
        "depends_on",
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        nullable=True,
    )

    # op.alter_column(
    #     "documents",
    #     "embedding_status",
    #     existing_type=embedding_status,
    #     type_=sa.String(length=20),
    #     existing_nullable=False,
    #     existing_server_default=sa.text("'PENDING'::embeddingstatus"),
    #     postgresql_using="embedding_status::text",
    # )

    op.alter_column(
        "documents",
        "status",
        existing_type=document_status,
        type_=sa.String(length=50),
        existing_nullable=False,
        postgresql_using="status::text",
    )

    embedding_status.drop(op.get_bind(), checkfirst=True)
    document_status.drop(op.get_bind(), checkfirst=True)