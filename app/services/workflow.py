from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import Workflow
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

        result = await db.execute(
            select(Workflow).where(Workflow.id == workflow_id)
        )

        workflow = result.scalar_one_or_none()

        if not workflow:
            raise ValueError("Workflow not found")

        # SIMPLE v1 prompt (no chaining yet)
        prompt = f"""
You are executing a workflow: {workflow.name}

User input:
{user_input}

Return a high-quality structured response.
"""

        response = await self.ai.generate_chat_response(
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response