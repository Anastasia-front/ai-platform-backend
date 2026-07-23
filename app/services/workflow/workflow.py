import asyncio

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import WorkflowRunStatus
from app.models import WorkflowRun
from app.repositories import (
    WorkflowRunRepository,
)
from app.schemas import WorkflowRunResponse
from app.services.background_jobs import BackgroundJobService
from app.services.workflow import DAGEngine, EventBus


class WorkflowService:
    DELETABLE_STATUSES = {
        WorkflowRunStatus.COMPLETED,
        WorkflowRunStatus.FAILED,
        WorkflowRunStatus.CANCELED,
        WorkflowRunStatus.PAUSED,
    }
    ACTIVE_STATUSES = {
        WorkflowRunStatus.PENDING,
        WorkflowRunStatus.RUNNING,
    }

    def __init__(
        self,
        runs: WorkflowRunRepository,
        events: EventBus,
        engine: DAGEngine,
    ):
        self.runs = runs
        self.events = events
        self.engine = engine

    @staticmethod
    def run_response(
        workflow_run: WorkflowRun,
        output: str | None = None,
    ) -> WorkflowRunResponse:
        return WorkflowRunResponse(
            id=workflow_run.id,
            workflow_id=workflow_run.workflow_id,
            input=workflow_run.input,
            output=workflow_run.output if output is None else output,
            status=workflow_run.status,
            celery_task_id=workflow_run.celery_task_id,
            error=workflow_run.error,
            created_at=workflow_run.created_at,
        )

    async def create_run(
        self,
        db: AsyncSession,
        workflow_id: int,
        user_input: str,
    ) -> WorkflowRun:
        """Create a PENDING run row only. Does not execute it.

        Used by the API layer so a run can be created, its Celery task
        enqueued, and HTTP 202 returned immediately -- without ever running
        the workflow inline inside the request.
        """
        return await self.runs.create(
            db=db,
            workflow_id=workflow_id,
            user_input=user_input,
        )

    async def enqueue_run(
        self,
        db: AsyncSession,
        workflow_id: int,
        user_input: str,
        jobs: BackgroundJobService,
    ) -> WorkflowRun:
        from app.tasks.workflows import run_workflow_task

        workflow_run = await self.runs.create_committed(
            db=db,
            workflow_id=workflow_id,
            user_input=user_input,
        )

        try:
            task = jobs.enqueue(run_workflow_task, workflow_run.id)
        except HTTPException:
            await self.runs.fail_with_error(
                db,
                workflow_run,
                "Background job queue is unavailable.",
            )
            raise

        return await self.runs.set_task_id(db, workflow_run, task.id)

    async def enqueue_resume(
        self,
        db: AsyncSession,
        workflow_run: WorkflowRun,
        jobs: BackgroundJobService,
    ) -> WorkflowRun:
        from app.tasks.workflows import resume_workflow_task

        if workflow_run.status not in (
            WorkflowRunStatus.FAILED,
            WorkflowRunStatus.PAUSED,
            WorkflowRunStatus.CANCELED,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Run is not resumable from status '{workflow_run.status}'.",
            )

        previous_status = workflow_run.status
        await self.runs.start(db, workflow_run)

        try:
            task = jobs.enqueue(resume_workflow_task, workflow_run.id)
        except HTTPException:
            await self.runs.set_status(db, workflow_run, previous_status)
            raise

        return await self.runs.set_task_id(db, workflow_run, task.id)

    async def enqueue_retry(
        self,
        db: AsyncSession,
        workflow_run: WorkflowRun,
        jobs: BackgroundJobService,
    ) -> WorkflowRun:
        return await self.enqueue_run(
            db=db,
            workflow_id=workflow_run.workflow_id,
            user_input=workflow_run.input,
            jobs=jobs,
        )

    async def cancel_run(
        self,
        db: AsyncSession,
        workflow_run: WorkflowRun,
        jobs: BackgroundJobService,
    ) -> WorkflowRun:
        if workflow_run.status == WorkflowRunStatus.CANCELED:
            return workflow_run

        if workflow_run.status not in (
            WorkflowRunStatus.PENDING,
            WorkflowRunStatus.RUNNING,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Run is not cancelable from status '{workflow_run.status}'.",
            )

        workflow_run = await self.runs.cancel(db, workflow_run)

        if workflow_run.celery_task_id:
            jobs.revoke(workflow_run.celery_task_id, terminate=True)

        return workflow_run

    async def delete_run(
        self,
        db: AsyncSession,
        workflow_run: WorkflowRun,
    ) -> None:
        if workflow_run.status in self.ACTIVE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Stop or cancel this execution before deleting it permanently.",
            )

        if workflow_run.status not in self.DELETABLE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Run is not deletable from status '{workflow_run.status}'.",
            )

        await self.runs.delete(db, workflow_run)

    async def delete_canceled_runs(
        self,
        db: AsyncSession,
        user_id: int,
        project_id: int | None = None,
    ) -> int:
        return await self.runs.delete_for_user_by_status(
            db=db,
            user_id=user_id,
            status=WorkflowRunStatus.CANCELED,
            project_id=project_id,
        )

    async def execute_run(
        self,
        db: AsyncSession,
        workflow_run: WorkflowRun,
        max_retries: int = 3,
        continue_on_error: bool = True,
    ) -> WorkflowRun:
        """Run the DAG engine for an already-created run and persist status.

        This is the body a Celery worker calls once it actually starts
        working on a queued run -- status only flips to RUNNING here, not
        when the run row/task is created.
        """
        await self.runs.start(db, workflow_run)

        try:
            output = await self.engine.execute(
                db=db,
                workflow_run=workflow_run,
                workflow_id=workflow_run.workflow_id,
                user_input=workflow_run.input,
                max_retries=max_retries,
                continue_on_error=continue_on_error,
            )
        except Exception as exc:
            await self.runs.fail_with_error(db, workflow_run, str(exc))
            raise

        await self.events.emit(
            db,
            workflow_run.id,
            "workflow_done",
            {
                "output": output,
            },
        )

        return await self.runs.commit_complete(
            db=db,
            workflow_run=workflow_run,
            output=output or "",
        )

    async def run_workflow(
        self,
        db: AsyncSession,
        workflow_id: int,
        user_input: str,
        max_retries: int = 3,
        continue_on_error: bool = True,
    ):
        workflow_run = await self.create_run(
            db=db,
            workflow_id=workflow_id,
            user_input=user_input,
        )

        return await self.execute_run(
            db=db,
            workflow_run=workflow_run,
            max_retries=max_retries,
            continue_on_error=continue_on_error,
        )

    async def run_workflow_stream(
        self,
        db: AsyncSession,
        workflow_id: int,
        user_input: str,
        max_retries: int = 3,
        continue_on_error: bool = True,
    ):

        workflow_run = await self.runs.create(
            db=db,
            workflow_id=workflow_id,
            user_input=user_input,
        )

        async def execute_and_emit():
            try:
                await self.events.emit(
                    db,
                    workflow_run.id,
                    "workflow_queued",
                    {
                        "run_id": workflow_run.id,
                        "workflow_id": workflow_id,
                        "message": "Workflow queued",
                        "progress": 0,
                    },
                )
                await self.runs.start(db, workflow_run)
                await self.events.emit(
                    db,
                    workflow_run.id,
                    "workflow_started",
                    {
                        "run_id": workflow_run.id,
                        "workflow_id": workflow_id,
                        "message": "Workflow started",
                        "progress": 5,
                    },
                )

                output = await self.engine.execute(
                    db=db,
                    workflow_run=workflow_run,
                    workflow_id=workflow_id,
                    user_input=user_input,
                    max_retries=max_retries,
                    continue_on_error=continue_on_error,
                )

                await self.runs.complete(
                    db=db,
                    workflow_run=workflow_run,
                    output=output or "",
                )

                await self.events.emit(
                    db,
                    workflow_run.id,
                    "workflow_done",
                    {
                        "run_id": workflow_run.id,
                        "workflow_id": workflow_id,
                        "message": "Workflow completed",
                        "progress": 100,
                        "output": output or "",
                    },
                )

                await self.runs.commit_complete(
                    db=db,
                    workflow_run=workflow_run,
                    output=output or "",
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                await self.runs.fail_with_error(db, workflow_run, str(exc))
                await self.events.emit(
                    db,
                    workflow_run.id,
                    "workflow_failed",
                    {
                        "run_id": workflow_run.id,
                        "workflow_id": workflow_id,
                        "message": "Workflow failed",
                        "error": str(exc),
                    },
                )

        terminal_markers = (
            "event: completed\n",
            "event: failed\n",
            "event: cancelled\n",
        )
        async with self.events.subscribe(workflow_run.id) as queue:
            task = asyncio.create_task(execute_and_emit())
            try:
                while True:
                    frame = await queue.get()
                    yield frame
                    if frame.startswith(terminal_markers):
                        break
                await task
            finally:
                pass

    async def run_workflow_stream_until_disconnected(
        self,
        db: AsyncSession,
        *,
        workflow_id: int,
        user_input: str,
        is_disconnected,
    ):
        async for event in self.run_workflow_stream(
            db=db,
            workflow_id=workflow_id,
            user_input=user_input,
        ):
            if await is_disconnected():
                break
            yield event

    async def resume_run(
        self,
        db: AsyncSession,
        workflow_run: WorkflowRun,
    ) -> WorkflowRun:
        """Resume an already-claimed (RUNNING) run. Status transitions and
        claiming happen in the caller (endpoint claims PENDING/FAILED/PAUSED
        -> RUNNING before enqueuing; the task calls this once it starts)."""

        try:
            output = await self.engine.execute(
                db=db,
                workflow_run=workflow_run,
                workflow_id=workflow_run.workflow_id,
                user_input=workflow_run.input,
                max_retries=3,
                continue_on_error=True,
            )
        except Exception as exc:
            await self.runs.fail_with_error(db, workflow_run, str(exc))
            raise

        return await self.runs.commit_complete(
            db=db,
            workflow_run=workflow_run,
            output=output or "",
        )

    async def resume_workflow(
        self,
        db: AsyncSession,
        run_id: int,
    ):
        """Kept for backward compatibility with any direct/synchronous
        callers; the API endpoint now claims + enqueues instead."""

        workflow_run = await self.runs.get_by_id(
            db,
            run_id,
        )

        if not workflow_run:
            raise ValueError("Workflow run not found")

        await self.runs.start(db, workflow_run)

        workflow_run = await self.resume_run(db, workflow_run)
        return workflow_run.output
