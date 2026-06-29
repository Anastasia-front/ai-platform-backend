from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base, settings
from app.models.mixins import TimestampMixin


class ChunkEmbedding(TimestampMixin, Base):
    __tablename__ = "chunk_embeddings"

    __table_args__ = (
        UniqueConstraint(
            "chunk_id",
            "provider",
            "model_name",
            name="uq_chunk_embedding_provider_model",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    chunk_id: Mapped[int] = mapped_column(
        ForeignKey("document_chunks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dimensions: Mapped[int] = mapped_column(nullable=False)

    embedding: Mapped[list[float]] = mapped_column(
        Vector(settings.EMBEDDING_DIM),
        nullable=False,
    )

    chunk = relationship("DocumentChunk", back_populates="embeddings")
