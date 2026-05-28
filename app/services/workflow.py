import asyncio
import json
import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    WorkflowRun,
    WorkflowRunEvent,
    WorkflowStep,
    WorkflowStepRun,
)
from app.services import AIService


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

        db.add(
            WorkflowRunEvent(
                workflow_run_id=workflow_run_id,
                event_type=event_type,
                payload=data,
            )
        )

        await db.flush()

        return (
            f"event: {event_type}\n"
            f"data: {json.dumps(data)}\n\n"
        )

    # =========================================================
    # DAG UTILITIES
    # =========================================================

    def _detect_cycles(self, steps: list[WorkflowStep]):
        graph = {s.id: set(s.depends_on or []) for s in steps}

        visited = set()
        stack = set()

        def dfs(node):
            if node in stack:
                raise Exception("Cycle detected in workflow DAG")
            if node in visited:
                return

            visited.add(node)
            stack.add(node)

            for dep in graph.get(node, []):
                dfs(dep)

            stack.remove(node)

        for node in graph:
            dfs(node)

    def _evaluate_condition(
        self,
        condition: str | None,
        completed_outputs: dict[int, Any],
        user_input: str,
    ) -> bool:
        """
        SAFE SIMPLE CONDITION ENGINE (replace later with AST sandbox)
        """
        if not condition:
            return True

        context = {
            "input": user_input,
            "outputs": completed_outputs,
        }

        try:
            return bool(eval(condition, {"__builtins__": {}}, context))
        except Exception:
            return False

    def _ready_steps(
        self,
        pending: dict[int, WorkflowStep],
        completed: set[int],
        outputs: dict[int, Any],
        user_input: str,
    ):
        ready = []

        for step in pending.values():

            deps = step.depends_on or []

            if not all(dep in completed for dep in deps):
                continue

            if not self._evaluate_condition(
                step.condition,
                outputs,
                user_input,
            ):
                continue

            ready.append(step)

        return ready

    # =========================================================
    # STEP EXECUTOR (isolated unit)
    # =========================================================
    async def _execute_single_step(
        self,
        db: AsyncSession,
        workflow_run: WorkflowRun,
        step: WorkflowStep,
        user_input: str,
        dependency_outputs: dict[int, Any],
        max_retries: int,
        continue_on_error: bool,
    ):
        await self._emit_event(
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
        prompt = prompt.replace("{{input}}", user_input)
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
                ai_output = await self.ai.generate_chat_response(
                    messages=[{"role": "user", "content": prompt}]
                )
                success = True

            except Exception as e:
                attempt += 1
                error_message = str(e)

                await self._emit_event(
                    db,
                    workflow_run.id,
                    "retry",
                    {
                        "step_id": step.id,
                        "attempt": attempt,
                        "error": error_message,
                    },
                )

                if attempt >= max_retries and not continue_on_error:
                    raise

        execution_time_ms = int((time.time() - start) * 1000)

        db.add(
            WorkflowStepRun(
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
        )

        await db.flush()

        if success:
            await self._emit_event(
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
            await self._emit_event(
                db,
                workflow_run.id,
                "step_error",
                {
                    "step_id": step.id,
                    "error": error_message,
                },
            )

        return step.id, ai_output, success

    # =========================================================
    # DAG EXECUTION ENGINE
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
        )

        steps = result.scalars().all()

        # ---------------------------
        # DAG validation
        # ---------------------------
        self._detect_cycles(steps)

        pending = {s.id: s for s in steps}
        completed = set()
        outputs = {}

        final_output = None

        # ---------------------------
        # DAG loop
        # ---------------------------
        while pending:

            ready = self._ready_steps(
                pending,
                completed,
                outputs,
                user_input,
            )

            if not ready:
                raise Exception(
                    "Deadlock: no executable steps (check dependencies/conditions)"
                )

            for step in ready:
                pending.pop(step.id)

            # ---------------------------
            # PARALLEL EXECUTION
            # ---------------------------
            results = await asyncio.gather(
                *[
                    self._execute_single_step(
                        db,
                        workflow_run,
                        step,
                        user_input,
                        {
                            dep: outputs.get(dep)
                            for dep in (step.depends_on or [])
                        },
                        max_retries,
                        continue_on_error,
                    )
                    for step in ready
                ]
            )

            # ---------------------------
            # merge results
            # ---------------------------
            for step_id, output, success in results:

                completed.add(step_id)
                outputs[step_id] = output
                final_output = output or final_output

        workflow_run.output = final_output or ""
        workflow_run.status = "completed"

        await db.commit()

        await self._emit_event(
            db,
            workflow_run.id,
            "workflow_done",
            {"output": final_output},
        )

        yield await self._emit_event(
            db,
            workflow_run.id,
            "workflow_done",
            {"output": final_output},
        )

    # =========================================================
    # RUN (NON-STREAM)
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
            db,
            workflow_run,
            workflow_id,
            user_input,
            max_retries,
            continue_on_error,
        ):
            if "workflow_done" in event:
                payload = json.loads(event.split("\n")[1].replace("data: ", ""))
                final_output = payload.get("output")

        return final_output or ""

    # =========================================================
    # STREAM
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
            db,
            workflow_run,
            workflow_id,
            user_input,
            max_retries,
            continue_on_error,
        ):
            yield event