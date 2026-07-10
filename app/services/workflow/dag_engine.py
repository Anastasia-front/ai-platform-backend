import asyncio

from simpleeval import simple_eval
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import WorkflowRunStatus
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
                raise ValueError(
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

    def validate_dependencies(
        self,
        steps: list[WorkflowStep],
    ):
        step_ids = {
            step.id
            for step in steps
        }

        missing_dependencies = {
            step.id: [
                dep
                for dep in (step.depends_on or [])
                if dep not in step_ids
            ]
            for step in steps
        }
        missing_dependencies = {
            step_id: deps
            for step_id, deps in missing_dependencies.items()
            if deps
        }

        if missing_dependencies:
            details = ", ".join(
                f"step {step_id} depends on missing step(s) {deps}"
                for step_id, deps in missing_dependencies.items()
            )
            raise ValueError(
                f"Invalid workflow DAG: {details}"
            )

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

    def get_skipped_steps(
        self,
        pending_steps,
        completed_steps,
        outputs,
        user_input,
    ):
        skipped = []

        for step in pending_steps.values():

            deps = step.depends_on or []

            if not all(
                dep in completed_steps
                for dep in deps
            ):
                continue

            if self.evaluate_condition(
                step.condition,
                outputs,
                user_input,
            ):
                continue

            skipped.append(step)

        return skipped

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

        steps = await self.steps.list_for_workflow(
            db,
            workflow_id,
        )

        if not steps:
            workflow_run.status = WorkflowRunStatus.COMPLETED
            workflow_run.output = ""
            await db.flush()
            return ""

        self.validate_dependencies(steps)
        self.detect_cycles(steps)

        pending_steps = {
            step.id: step
            for step in steps
        }


        # persistent DAG state
        completed_runs = (
            await self.step_runs.list_completed_for_run(
                db,
                workflow_run.id,
            )
        )

        completed_steps = {
            run.workflow_step_id
            for run in completed_runs
            if run.status == WorkflowRunStatus.COMPLETED
        }

        completed_outputs = {
            run.workflow_step_id: run.output
            for run in completed_runs
            if run.status == WorkflowRunStatus.COMPLETED
        }

        # remove already executed nodes
        for step_id in completed_steps:
            pending_steps.pop(step_id, None)

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

            skipped_steps = self.get_skipped_steps(
                pending_steps,
                completed_steps,
                completed_outputs,
                user_input,
            )

            if not ready_steps and not skipped_steps:
                raise ValueError(
                    "Deadlock detected in DAG"
                )

            for step in skipped_steps:
                pending_steps.pop(step.id)
                completed_steps.add(step.id)

                await self.events.emit(
                    db,
                    workflow_run.id,
                    "step_skipped",
                    {
                        "step_id": step.id,
                        "name": step.name,
                        "condition": step.condition,
                    },
                )

            if not ready_steps:
                await db.flush()
                continue

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
            tasks = []

            for step in ready_steps:

                tasks.append(
                    self.executor.execute(
                        step=step,
                        user_input=user_input,
                        dependency_outputs={
                            dep: completed_outputs.get(dep)
                            for dep in (step.depends_on or [])
                        },
                        max_retries=max_retries,
                        continue_on_error=continue_on_error,
                    )
                )

            raw_results = await asyncio.gather(
                *tasks,
                return_exceptions=True,
            )

            results = []

            for step, result in zip(
                ready_steps,
                raw_results,
            ):

                if isinstance(result, Exception):

                    results.append(
                        {
                            "step_id": step.id,
                            "step_order": step.step_order,
                            "prompt": step.prompt_template,
                            "success": False,
                            "output": None,
                            "execution_time_ms": 0,
                            "retry_count": max_retries,
                            "error_message": str(result),
                        }
                    )

                else:

                    results.append(result)

            # -----------------------------------------
            # persist results
            # -----------------------------------------

            for result in results:
                existing = await self.step_runs.get_step_run(
                    db=db,
                    workflow_run_id=workflow_run.id,
                    workflow_step_id=result["step_id"],
                )

                if existing and existing.status == WorkflowRunStatus.COMPLETED:
                    continue
                
                await self.step_runs.create(
                    db=db,
                    workflow_run_id=workflow_run.id,
                    workflow_step_id=result["step_id"],
                    step_order=result["step_order"],
                    input=result["prompt"],
                    output=result["output"],
                    status=WorkflowRunStatus.COMPLETED if result["success"] else WorkflowRunStatus.FAILED,
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

                    if continue_on_error:
                        completed_steps.add(
                            result["step_id"]
                        )

                    if not continue_on_error:

                        workflow_run.status = WorkflowRunStatus.FAILED

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
