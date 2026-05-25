from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WorkflowRunEvent(Base):
    __tablename__ = "workflow_run_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    workflow_run_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_runs.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(String, nullable=False)

    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )