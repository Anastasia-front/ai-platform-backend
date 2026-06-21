from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base
from app.models.mixins import TimestampMixin


class ChunkEmbedding(TimestampMixin, Base):
    __tablename__ = "chunk_embeddings"

    id: Mapped[int] = mapped_column(primary_key=True)

    chunk_id: Mapped[int] = mapped_column(
        ForeignKey("document_chunks.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    model_name: Mapped[str] = mapped_column(String(100), nullable=False)

    embedding: Mapped[list[float]] = mapped_column(
        Vector(1536),
        nullable=False,
    )

    chunk = relationship(
        "DocumentChunk",
        back_populates="embedding"
    )