from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class WorkflowRunEvent(TimestampMixin, Base):
    __tablename__ = "workflow_run_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    workflow_run_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_runs.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(String, nullable=False)

    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
