from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base
from app.enums import DocumentStatus, EmbeddingStatus
from app.models.mixins import TimestampMixin


class Document(TimestampMixin, Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    filename: Mapped[str] = mapped_column(String(255), nullable=False)

    filepath: Mapped[str] = mapped_column(String(1024), nullable=False)

    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)

    file_size: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[DocumentStatus] = mapped_column(
        Enum(
            DocumentStatus,
            name="documentstatus",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        default=DocumentStatus.UPLOADED,
        nullable=False,
    )

    text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    processing_started_at = mapped_column(DateTime(timezone=True), nullable=True)
    processing_finished_at = mapped_column(DateTime(timezone=True), nullable=True)
    processing_duration_ms = mapped_column(Integer, nullable=True)

    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    embedding_status: Mapped[EmbeddingStatus] = mapped_column(
        Enum(
            EmbeddingStatus,
            name="embeddingstatus",
            values_callable=lambda x: [e.value for e in x],
            native_enum=True,
            create_type=False,
        ),
        default=EmbeddingStatus.PENDING,
        nullable=False,
    )

    project = relationship(
        "Project",
        back_populates="documents",
    )

    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="DocumentChunk.chunk_index",
    )
