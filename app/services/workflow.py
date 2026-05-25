import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow_run import WorkflowRun
from app.models.workflow_step import WorkflowStep
from app.models.workflow_step_run import WorkflowStepRun
from app.services.ai import AIService


class WorkflowService:

    def __init__(self):
        self.ai = AIService()

    async def run_workflow(
        self,
        db: AsyncSession,
        workflow_id: int,
        user_input: str,
        max_retries: int = 3,
        continue_on_error: bool = True,
    ) -> str:

        # 1. load steps
        result = await db.execute(
            select(WorkflowStep)
            .where(WorkflowStep.workflow_id == workflow_id)
            .order_by(WorkflowStep.step_order)
        )
        steps = result.scalars().all()

        # 2. create run
        workflow_run = WorkflowRun(
            workflow_id=workflow_id,
            input=user_input,
            status="running",
        )

        db.add(workflow_run)
        await db.flush()

        previous_output = user_input
        final_output = None

        # 3. execute steps
        for step in steps:

            prompt = step.prompt_template
            prompt = prompt.replace("{{input}}", user_input)
            prompt = prompt.replace("{{previous_output}}", previous_output)

            attempt = 0
            success = False
            ai_output = None
            error_message = None

            start = time.time()

            while attempt < max_retries and not success:
                try:
                    ai_output = await self.ai.generate_chat_response(
                        messages=[{"role": "user", "content": prompt}]
                    )
                    success = True

                except Exception as e:
                    attempt += 1
                    error_message = str(e)

                    if attempt >= max_retries:
                        if not continue_on_error:
                            raise

            execution_time_ms = int((time.time() - start) * 1000)

            step_run = WorkflowStepRun(
                workflow_run_id=workflow_run.id,
                workflow_step_id=step.id,
                step_order=step.step_order,
                input=prompt,
                output=ai_output,
                status="completed" if success else "failed",
                execution_time_ms=execution_time_ms,
                retry_count=attempt,
                error_message=error_message,
            )

            db.add(step_run)

            # decide flow continuation
            if success:
                previous_output = ai_output
                final_output = ai_output
            else:
                if not continue_on_error:
                    workflow_run.status = "failed"
                    await db.commit()
                    raise Exception(f"Step failed: {step.name}")

        # 4. finalize run
        workflow_run.output = final_output
        workflow_run.status = "completed"

        await db.commit()

        return final_output