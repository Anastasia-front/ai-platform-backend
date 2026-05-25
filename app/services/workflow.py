import json
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow_run import WorkflowRun
from app.models.workflow_run_event import WorkflowRunEvent
from app.models.workflow_step import WorkflowStep
from app.models.workflow_step_run import WorkflowStepRun
from app.services.ai import AIService


class WorkflowService:

    def __init__(self):
        self.ai = AIService()

    # =========================================================
    # EVENT BUS
    # =========================================================
    async def _emit_event(
        self,
        db: AsyncSession,
        workflow_run_id: int,
        event_type: str,
        data: dict,
    ) -> str:

        # persist event
        db.add(
            WorkflowRunEvent(
                workflow_run_id=workflow_run_id,
                event_type=event_type,
                payload=data,
            )
        )

        await db.flush()

        # SSE format
        return (
            f"event: {event_type}\n"
            f"data: {json.dumps(data)}\n\n"
        )

    # =========================================================
    # INTERNAL EXECUTION ENGINE
    # =========================================================
    async def _execute_steps(
        self,
        db: AsyncSession,
        workflow_run: WorkflowRun,
        workflow_id: int,
        user_input: str,
        max_retries: int = 3,
        continue_on_error: bool = True,
    ):

        result = await db.execute(
            select(WorkflowStep)
            .where(WorkflowStep.workflow_id == workflow_id)
            .order_by(WorkflowStep.step_order)
        )

        steps = result.scalars().all()

        previous_output = user_input
        final_output = None

        for step in steps:

            # -------------------------------------
            # STEP START
            # -------------------------------------
            yield await self._emit_event(
                db=db,
                workflow_run_id=workflow_run.id,
                event_type="step_start",
                data={
                    "step_id": step.id,
                    "name": step.name,
                    "order": step.step_order,
                },
            )

            prompt = step.prompt_template
            prompt = prompt.replace(
                "{{input}}",
                user_input,
            )

            prompt = prompt.replace(
                "{{previous_output}}",
                previous_output,
            )

            attempt = 0
            success = False
            ai_output = None
            error_message = None

            start = time.time()

            # -------------------------------------
            # RETRY LOOP
            # -------------------------------------
            while attempt < max_retries and not success:

                try:

                    ai_output = (
                        await self.ai.generate_chat_response(
                            messages=[
                                {
                                    "role": "user",
                                    "content": prompt,
                                }
                            ]
                        )
                    )

                    success = True

                except Exception as e:

                    attempt += 1
                    error_message = str(e)

                    yield await self._emit_event(
                        db=db,
                        workflow_run_id=workflow_run.id,
                        event_type="retry",
                        data={
                            "step_id": step.id,
                            "attempt": attempt,
                            "error": error_message,
                        },
                    )

                    if (
                        attempt >= max_retries
                        and not continue_on_error
                    ):
                        raise

            execution_time_ms = int(
                (time.time() - start) * 1000
            )

            # -------------------------------------
            # STEP RUN PERSISTENCE
            # -------------------------------------
            step_run = WorkflowStepRun(
                workflow_run_id=workflow_run.id,
                workflow_step_id=step.id,
                step_order=step.step_order,
                input=prompt,
                output=ai_output,
                status=(
                    "completed"
                    if success
                    else "failed"
                ),
                execution_time_ms=execution_time_ms,
                retry_count=attempt,
                error_message=error_message,
            )

            db.add(step_run)

            # -------------------------------------
            # STEP SUCCESS
            # -------------------------------------
            if success:

                previous_output = ai_output
                final_output = ai_output

                yield await self._emit_event(
                    db=db,
                    workflow_run_id=workflow_run.id,
                    event_type="step_done",
                    data={
                        "step_id": step.id,
                        "output": ai_output,
                        "execution_time_ms": execution_time_ms,
                    },
                )

            # -------------------------------------
            # STEP FAILURE
            # -------------------------------------
            else:

                yield await self._emit_event(
                    db=db,
                    workflow_run_id=workflow_run.id,
                    event_type="step_error",
                    data={
                        "step_id": step.id,
                        "error": error_message,
                    },
                )

                if not continue_on_error:

                    workflow_run.status = "failed"

                    await db.commit()

                    raise Exception(
                        f"Step failed: {step.name}"
                    )

        # =====================================================
        # FINALIZE WORKFLOW
        # =====================================================
        workflow_run.output = final_output
        workflow_run.status = "completed"

        await db.commit()

        yield await self._emit_event(
            db=db,
            workflow_run_id=workflow_run.id,
            event_type="workflow_done",
            data={
                "output": final_output,
            },
        )

    # =========================================================
    # NORMAL EXECUTION
    # =========================================================
    async def run_workflow(
        self,
        db: AsyncSession,
        workflow_id: int,
        user_input: str,
        max_retries: int = 3,
        continue_on_error: bool = True,
    ) -> str:

        workflow_run = WorkflowRun(
            workflow_id=workflow_id,
            input=user_input,
            status="running",
        )

        db.add(workflow_run)

        await db.flush()

        final_output = None

        async for event in self._execute_steps(
            db=db,
            workflow_run=workflow_run,
            workflow_id=workflow_id,
            user_input=user_input,
            max_retries=max_retries,
            continue_on_error=continue_on_error,
        ):

            # parse workflow_done event
            if "workflow_done" in event:

                data_line = event.split("\n")[1]
                json_data = data_line.replace(
                    "data: ",
                    "",
                )

                payload = json.loads(json_data)

                final_output = payload["output"]

        return final_output

    # =========================================================
    # STREAMING EXECUTION
    # =========================================================
    async def run_workflow_stream(
        self,
        db: AsyncSession,
        workflow_id: int,
        user_input: str,
        max_retries: int = 3,
        continue_on_error: bool = True,
    ):

        workflow_run = WorkflowRun(
            workflow_id=workflow_id,
            input=user_input,
            status="running",
        )

        db.add(workflow_run)

        await db.flush()

        async for event in self._execute_steps(
            db=db,
            workflow_run=workflow_run,
            workflow_id=workflow_id,
            user_input=user_input,
            max_retries=max_retries,
            continue_on_error=continue_on_error,
        ):
            yield event