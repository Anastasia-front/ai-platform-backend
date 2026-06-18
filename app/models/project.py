from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
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
