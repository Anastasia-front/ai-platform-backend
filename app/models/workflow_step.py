from sqlalchemy import (
    JSON,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class WorkflowStep(TimestampMixin, Base):
    __tablename__ = "workflow_steps"

    __table_args__ = (
        Index("ix_workflow_steps_workflow_order", "workflow_id", "step_order"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    step_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    prompt_template: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    depends_on: Mapped[list[int]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )

    condition: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    workflow = relationship(
        "Workflow",
        back_populates="steps",
    )
