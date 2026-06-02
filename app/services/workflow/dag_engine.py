import asyncio

from simpleeval import simple_eval
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import WorkflowRun, WorkflowStep
from app.repositories import (
    WorkflowStepRepository,
    WorkflowStepRunRepository,
)
from app.services.workflow.ai_executor import AIExecutor
from app.services.workflow.event_bus import EventBus


class DAGEngine:

    def __init__(self):
        self.executor = AIExecutor()
        self.events = EventBus()

        self.steps = WorkflowStepRepository()
        self.step_runs = WorkflowStepRunRepository()

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

    ALLOWED_FUNCTIONS = {
        "len": len,
    }

    def evaluate_condition(
        self,
        condition: str | None,
        outputs: dict,
        user_input: str,
    ) -> bool:

        if not condition:
            return True

        try:
            return bool(
                simple_eval(
                    condition,
                    names={
                        "input": user_input,
                        "outputs": outputs,
                    },
                    functions=self.ALLOWED_FUNCTIONS,
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

        steps = await self.steps.get_workflow_steps(
            db,
            workflow_id,
        )

        if not steps:
            workflow_run.status = "completed"
            workflow_run.output = ""
            await db.flush()
            return ""

        self.detect_cycles(steps)

        pending_steps = {
            step.id: step
            for step in steps
        }

        completed_steps = set()
        completed_outputs = {}

        # terminal nodes = steps nobody depends on
        terminal_steps = [
            step.id
            for step in steps
            if not any(
                step.id in (other.depends_on or [])
                for other in steps
            )
        ]

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

            # remove from pending
            for step in ready_steps:
                pending_steps.pop(step.id)

            # -----------------------------------------
            # emit start events
            # -----------------------------------------
            for step in ready_steps:

                await self.events.emit(
                    db,
                    workflow_run.id,
                    "step_start",
                    {
                        "step_id": step.id,
                        "name": step.name,
                        "dependencies": (
                            step.depends_on or []
                        ),
                    },
                )

            await db.flush()

            # -----------------------------------------
            # execute AI tasks in parallel
            # -----------------------------------------
            results = await asyncio.gather(
                *[
                    self.executor.execute(
                        step=step,
                        user_input=user_input,
                        dependency_outputs={
                            dep: completed_outputs.get(dep)
                            for dep in (
                                step.depends_on or []
                            )
                        },
                        max_retries=max_retries,
                        continue_on_error=continue_on_error,
                    )
                    for step in ready_steps
                ]
            )

            # -----------------------------------------
            # persist results
            # -----------------------------------------
            for result in results:

                await self.step_runs.create(
                    db=db,
                    workflow_run_id=workflow_run.id,
                    workflow_step_id=result["step_id"],
                    step_order=result["step_order"],
                    input=result["prompt"],
                    output=result["output"],
                    status="completed" if result["success"] else "failed",
                    execution_time_ms=result["execution_time_ms"],
                    retry_count=result["retry_count"],
                    error_message=result["error_message"],
                )
            await db.flush()

            # -----------------------------------------
            # process results
            # -----------------------------------------
            for result in results:

                if result["success"]:

                    completed_steps.add(
                        result["step_id"]
                    )

                    completed_outputs[
                        result["step_id"]
                    ] = result["output"]

                    await self.events.emit(
                        db,
                        workflow_run.id,
                        "step_done",
                        {
                            "step_id": result[
                                "step_id"
                            ],
                            "output": result[
                                "output"
                            ],
                            "execution_time_ms": result[
                                "execution_time_ms"
                            ],
                        },
                    )

                else:

                    await self.events.emit(
                        db,
                        workflow_run.id,
                        "step_error",
                        {
                            "step_id": result[
                                "step_id"
                            ],
                            "error": result[
                                "error_message"
                            ],
                        },
                    )

                    if not continue_on_error:

                        workflow_run.status = "failed"

                        await db.commit()

                        raise Exception(
                            f"Step failed: {result['step_id']}"
                        )

            await db.flush()

        # =====================================================
        # FINAL OUTPUT
        # =====================================================
        final_outputs = [
            completed_outputs[step_id]
            for step_id in terminal_steps
            if step_id in completed_outputs
            and completed_outputs[step_id]
        ]

        final_output = "\n\n".join(
            final_outputs
        )

        return final_output