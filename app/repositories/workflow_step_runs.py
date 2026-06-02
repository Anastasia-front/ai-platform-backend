from sqlalchemy.ext.asyncio import AsyncSession

from app.models import WorkflowStepRun


class WorkflowStepRunRepository:


    async def create(
        self,
        db: AsyncSession,
        **data,
    ):

        run = WorkflowStepRun(
            **data
        )

        db.add(run)

        await db.flush()

        return run