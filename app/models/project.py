from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.enums import EmbeddingStatus
from app.models.mixins import TimestampMixin


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    embedding_sync_status: Mapped[EmbeddingStatus] = mapped_column(
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
    embedding_sync_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    embedding_sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("User", back_populates="projects")

    workflows = relationship(
        "Workflow",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    chats = relationship(
        "Chat",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    documents = relationship(
        "Document",
        back_populates="project",
        cascade="all, delete-orphan",
    )
