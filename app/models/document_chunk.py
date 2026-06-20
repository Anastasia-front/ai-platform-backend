from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base
from app.models.mixins import TimestampMixin


class DocumentChunk(
    TimestampMixin,
    Base,
):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    token_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    start_offset = mapped_column(Integer, nullable=True)
    end_offset = mapped_column(Integer, nullable=True)

    # Later when using a vector database:
    embedding_id = mapped_column(String(255), nullable=True)

    document = relationship(
        "Document",
        back_populates="chunks",
    )
