from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String, nullable=False)

    status: Mapped[str] = mapped_column(
        String,
        default="pending",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # relations (optional but important for future expansion)
    agent_runs = relationship(
        "AgentRun",
        back_populates="workflow",
        cascade="all, delete-orphan",
    )

    project = relationship("Project", back_populates="workflows")

    steps = relationship(
    "WorkflowStep",
    back_populates="workflow",
    cascade="all, delete-orphan",
    order_by="WorkflowStep.step_order",
)
#     Later add:
# workflow_steps
# workflow_runs
# last_run_at
# run_count