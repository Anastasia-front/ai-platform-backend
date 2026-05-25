from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import Workflow
from app.models.workflow_step import WorkflowStep
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

        # load workflow
        workflow_result = await db.execute(
            select(Workflow).where(
                Workflow.id == workflow_id
            )
        )

        workflow = workflow_result.scalar_one_or_none()

        if not workflow:
            raise ValueError("Workflow not found")

        # load ordered steps
        steps_result = await db.execute(
            select(WorkflowStep)
            .where(WorkflowStep.workflow_id == workflow_id)
            .order_by(WorkflowStep.step_order)
        )

        steps = steps_result.scalars().all()

        # fallback if no steps
        if not steps:
            return await self.ai.generate_chat_response(
                messages=[
                    {
                        "role": "user",
                        "content": user_input,
                    }
                ]
            )

        previous_output = user_input

        for step in steps:

            prompt = (
                step.prompt_template
                .replace("{{input}}", user_input)
                .replace(
                    "{{previous_output}}",
                    previous_output,
                )
            )

            previous_output = await self.ai.generate_chat_response(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ]
            )

        return previous_output