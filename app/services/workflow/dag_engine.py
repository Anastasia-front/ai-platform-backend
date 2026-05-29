
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import WorkflowRun, WorkflowStep
from app.services.workflow.event_bus import EventBus
from app.services.workflow.step_executor import StepExecutor


class DAGEngine:

    def __init__(self):
        self.executor = StepExecutor()
        self.events = EventBus()

    # =====================================================
    # CYCLE DETECTION
    # =====================================================
    def detect_cycles(
        self,
        steps: list[WorkflowStep],
    ):

        graph = {
            step.id: set(step.depends_on or [])
            for step in steps
        }

        visited = set()
        stack = set()

        def dfs(node):

            if node in stack:
                raise Exception(
                    "Cycle detected in workflow DAG"
                )

            if node in visited:
                return

            visited.add(node)
            stack.add(node)

            for dep in graph.get(node, []):
                dfs(dep)

            stack.remove(node)

        for node in graph:
            dfs(node)

    # =====================================================
    # CONDITIONAL EXECUTION
    # =====================================================
    def evaluate_condition(
        self,
        condition,
        outputs,
        user_input,
    ):

        if not condition:
            return True

        context = {
            "input": user_input,
            "outputs": outputs,
        }

        try:
            return bool(
                eval(
                    condition,
                    {"__builtins__": {}},
                    context,
                )
            )
        except Exception:
            return False

    # =====================================================
    # READY STEP RESOLUTION
    # =====================================================
    def get_ready_steps(
        self,
        pending_steps,
        completed_steps,
        outputs,
        user_input,
    ):

        ready = []

        for step in pending_steps.values():

            deps = step.depends_on or []

            if not all(
                dep in completed_steps
                for dep in deps
            ):
                continue

            if not self.evaluate_condition(
                step.condition,
                outputs,
                user_input,
            ):
                continue

            ready.append(step)

        return ready

    # =====================================================
    # DAG EXECUTION
    # =====================================================
    async def execute(
        self,
        db: AsyncSession,
        workflow_run: WorkflowRun,
        workflow_id: int,
        user_input: str,
        max_retries: int,
        continue_on_error: bool,
    ):

        result = await db.execute(
            select(WorkflowStep)
            .where(
                WorkflowStep.workflow_id == workflow_id
            )
            .order_by(WorkflowStep.step_order)
        )

        steps = result.scalars().all()

        self.detect_cycles(steps)

        pending_steps = {
            step.id: step
            for step in steps
        }

        completed_steps = set()
        completed_outputs = {}

        final_output = None

        while pending_steps:

            ready_steps = self.get_ready_steps(
                pending_steps,
                completed_steps,
                completed_outputs,
                user_input,
            )

            if not ready_steps:
                raise Exception(
                    "Deadlock detected in DAG"
                )

            for step in ready_steps:
                pending_steps.pop(step.id)

            results = []

            for step in ready_steps:

                result = await self.executor.execute(
                  db=db,
                  workflow_run=workflow_run,
                  step=step,
                  user_input=user_input,
                  dependency_outputs=completed_outputs,
                  max_retries=max_retries,
                  continue_on_error=continue_on_error,
                )

                results.append(result)

            for result in results:

                if result["success"]:

                    completed_steps.add(
                        result["step_id"]
                    )

                    completed_outputs[
                        result["step_id"]
                    ] = result["output"]

                    final_output = result["output"]

        workflow_run.output = final_output or ""
        workflow_run.status = "completed"

        await db.commit()

        return final_output