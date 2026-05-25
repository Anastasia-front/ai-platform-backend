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
    ) -> str:

        # 1. load workflow steps
        result = await db.execute(
            select(WorkflowStep)
            .where(WorkflowStep.workflow_id == workflow_id)
            .order_by(WorkflowStep.step_order)
        )
        steps = result.scalars().all()

        # 2. create workflow run
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

            start = time.time()

            try:
                # -------------------------
                # AI CALL
                # -------------------------
                ai_output = await self.ai.generate_chat_response(
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                execution_time_ms = int((time.time() - start) * 1000)

                step_run = WorkflowStepRun(
                    workflow_run_id=workflow_run.id,
                    workflow_step_id=step.id,
                    step_order=step.step_order,
                    input=prompt,
                    output=ai_output,
                    status="completed",
                    execution_time_ms=execution_time_ms,
                    retry_count=0,
                    error_message=None,
                )

                previous_output = ai_output
                final_output = ai_output

            except Exception as e:

                execution_time_ms = int((time.time() - start) * 1000)

                step_run = WorkflowStepRun(
                    workflow_run_id=workflow_run.id,
                    workflow_step_id=step.id,
                    step_order=step.step_order,
                    input=prompt,
                    output=None,
                    status="failed",
                    execution_time_ms=execution_time_ms,
                    retry_count=0,
                    error_message=str(e),
                )

                # IMPORTANT: stop workflow on failure (simple mode)
                workflow_run.status = "failed"
                db.add(step_run)
                await db.commit()

                return f"Workflow failed at step {step.name}: {str(e)}"

            # persist step run
            db.add(step_run)

        # 4. finalize workflow run
        workflow_run.output = final_output
        workflow_run.status = "completed"

        await db.commit()

        return final_output