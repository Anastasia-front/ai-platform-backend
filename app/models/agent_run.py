from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.enums import WorkflowRunStatus
from app.models.mixins import TimestampMixin


class AgentRun(TimestampMixin, Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    goal: Mapped[str] = mapped_column(String, nullable=False)

    status: Mapped[str] = mapped_column(
        String,
        default=WorkflowRunStatus.PENDING,
        nullable=False,
    )

    result: Mapped[str | None] = mapped_column(String, nullable=True)

    # Optional relationship (useful later)
    workflow = relationship("Workflow", back_populates="agent_runs")
