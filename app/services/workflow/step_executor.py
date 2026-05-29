import json
import time
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import WorkflowRun, WorkflowStep, WorkflowStepRun
from app.services import AIService
from app.services.workflow.event_bus import EventBus


class StepExecutor:

    def __init__(self):
        self.ai = AIService()
        self.events = EventBus()

    async def execute(
        self,
        db: AsyncSession,
        workflow_run: WorkflowRun,
        step: WorkflowStep,
        user_input: str,
        dependency_outputs: dict[int, Any],
        max_retries: int,
        continue_on_error: bool,
    ):

        await self.events.emit(
            db,
            workflow_run.id,
            "step_start",
            {
                "step_id": step.id,
                "name": step.name,
                "dependencies": step.depends_on or [],
            },
        )

        prompt = step.prompt_template

        prompt = prompt.replace(
            "{{input}}",
            user_input,
        )

        prompt = prompt.replace(
            "{{dependency_outputs}}",
            json.dumps(dependency_outputs),
        )

        attempt = 0
        success = False
        ai_output = None
        error_message = None

        start = time.time()

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

                await self.events.emit(
                    db,
                    workflow_run.id,
                    "retry",
                    {
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

        db.add(
            WorkflowStepRun(
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
        )

        await db.flush()

        if success:

            await self.events.emit(
                db,
                workflow_run.id,
                "step_done",
                {
                    "step_id": step.id,
                    "output": ai_output,
                    "execution_time_ms": execution_time_ms,
                },
            )

        else:

            await self.events.emit(
                db,
                workflow_run.id,
                "step_error",
                {
                    "step_id": step.id,
                    "error": error_message,
                },
            )

        return {
            "step_id": step.id,
            "success": success,
            "output": ai_output,
        }