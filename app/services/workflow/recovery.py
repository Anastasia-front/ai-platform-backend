
import asyncio

from fastapi import Depends

from app.core.database import AsyncSessionLocal
from app.dependencies.workflow import get_workflow_service
from app.repositories import WorkflowRunRepository

from .workflow import WorkflowService


async def recover_running_workflows():

    async with AsyncSessionLocal() as db:

        runs_repo = WorkflowRunRepository()

        runs = await runs_repo.get_running(db)

    for run in runs:
        asyncio.create_task(
            resume_single_workflow(run.id)
        )


# bootstrap recovery
# create its own DB session
# call service
async def resume_single_workflow(run_id: int,
    service: WorkflowService = Depends(
    get_workflow_service
)):

    async with AsyncSessionLocal() as db:
        await service.resume_workflow(
            db=db,
            run_id=run_id,
        )