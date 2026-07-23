from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import DocumentStatus, EmbeddingStatus
from app.models import Workflow, WorkflowStep
from app.repositories import (
    DocumentRepository,
    WorkflowRepository,
    WorkflowRunRepository,
    WorkflowStepRepository,
)
from app.services.background_jobs import BackgroundJobService
from app.services.embedding import EmbeddingService
from app.services.workflow.workflow import WorkflowService


class ToolResult(BaseModel):
    tool: str
    status: str
    data: dict[str, Any]
    message: str | None = None

    model_config = ConfigDict(use_enum_values=True)


@dataclass(frozen=True)
class WorkspaceTool:
    name: str
    description: str
    read_only: bool = True


class WorkspaceToolRegistry:
    def __init__(
        self,
        *,
        documents: DocumentRepository,
        workflows: WorkflowRepository,
        workflow_steps: WorkflowStepRepository,
        workflow_runs: WorkflowRunRepository,
        workflow_service: WorkflowService,
        embedding_service: EmbeddingService,
        jobs: BackgroundJobService,
    ) -> None:
        self.documents = documents
        self.workflows = workflows
        self.workflow_steps = workflow_steps
        self.workflow_runs = workflow_runs
        self.workflow_service = workflow_service
        self.embedding_service = embedding_service
        self.jobs = jobs
        self.tools = {
            tool.name: tool
            for tool in (
                WorkspaceTool("list_project_documents", "List project documents"),
                WorkspaceTool("get_embedding_configuration", "Read active embedding provider config"),
                WorkspaceTool("check_embedding_rebuild_need", "Classify document embedding freshness"),
                WorkspaceTool("process_document", "Queue document processing", read_only=False),
                WorkspaceTool("rebuild_document_embeddings", "Queue document embedding rebuild", read_only=False),
                WorkspaceTool("sync_project_embeddings", "Queue project embedding sync", read_only=False),
                WorkspaceTool("list_workflows", "List project workflows"),
                WorkspaceTool("create_workflow", "Create workflow", read_only=False),
                WorkspaceTool("create_workflow_step", "Create workflow step", read_only=False),
                WorkspaceTool("run_workflow", "Queue workflow run", read_only=False),
                WorkspaceTool("list_workflow_runs", "List workflow runs"),
            )
        }

    async def list_project_documents(
        self,
        db: AsyncSession,
        *,
        project_id: int,
    ) -> ToolResult:
        documents = await self.documents.list_for_project(db, project_id)
        return ToolResult(
            tool="list_project_documents",
            status="completed",
            data={
                "documents": [self._document_summary(document) for document in documents],
            },
        )

    async def get_embedding_configuration(self) -> ToolResult:
        return ToolResult(
            tool="get_embedding_configuration",
            status="completed",
            data={
                "provider": self.embedding_service.provider,
                "model": self.embedding_service.model_name,
                "dimensions": self.embedding_service.dimensions,
            },
        )

    async def check_embedding_rebuild_need(
        self,
        db: AsyncSession,
        *,
        project_id: int,
    ) -> ToolResult:
        documents = await self.documents.list_for_project(db, project_id)
        current = {
            "provider": self.embedding_service.provider,
            "model": self.embedding_service.model_name,
            "dimensions": self.embedding_service.dimensions,
        }
        classified = {
            "current": [],
            "rebuild_required": [],
            "failed": [],
            "missing_embeddings": [],
            "unknown_metadata": [],
            "active_jobs": [],
            "not_ready": [],
        }

        for document in documents:
            summary = self._document_summary(document)
            if document.embedding_status in (EmbeddingStatus.QUEUED, EmbeddingStatus.PROCESSING):
                classified["active_jobs"].append(summary)
            elif document.status != DocumentStatus.INDEXED or not document.text:
                classified["not_ready"].append(summary)
            elif document.embedding_status == EmbeddingStatus.FAILED:
                classified["failed"].append(summary)
            elif not document.embedding_provider or not document.embedding_model or not document.embedding_dimensions:
                classified["unknown_metadata"].append(summary)
            elif (
                document.embedding_provider == current["provider"]
                and document.embedding_model == current["model"]
                and document.embedding_dimensions == current["dimensions"]
                and document.embedding_status == EmbeddingStatus.COMPLETED
            ):
                classified["current"].append(summary)
            elif document.embedding_status in (EmbeddingStatus.PENDING, EmbeddingStatus.CANCELLED):
                classified["missing_embeddings"].append(summary)
            else:
                classified["rebuild_required"].append(summary)

        return ToolResult(
            tool="check_embedding_rebuild_need",
            status="completed",
            data={
                "current_embedding_config": current,
                "classification": classified,
            },
        )

    async def update_files_for_embedding_model(
        self,
        db: AsyncSession,
        *,
        project_id: int,
    ) -> ToolResult:
        check = await self.check_embedding_rebuild_need(db, project_id=project_id)
        classification = check.data["classification"]
        rebuild_candidates = [
            *classification["rebuild_required"],
            *classification["missing_embeddings"],
            *classification["failed"],
            *classification["unknown_metadata"],
        ]
        queued = []
        failed = []

        for item in rebuild_candidates:
            document = await self.documents.get_by_id(db, item["id"])
            if document is None:
                failed.append({"id": item["id"], "error": "Document not found"})
                continue
            result = await self.rebuild_document_embeddings(db, document=document)
            if result.status in ("queued", "skipped"):
                queued.append(result.data)
            else:
                failed.append(result.data)

        return ToolResult(
            tool="update_files_for_embedding_model",
            status="completed" if not failed else "partial_failure",
            data={
                "queued_rebuilds": queued,
                "failed": failed,
                "already_current": classification["current"],
                "active_jobs": classification["active_jobs"],
                "not_ready": classification["not_ready"],
                "embedding_config": check.data["current_embedding_config"],
            },
        )

    async def process_document(
        self,
        db: AsyncSession,
        *,
        document,
    ) -> ToolResult:
        from app.tasks.documents import process_document_task

        if document.status in (DocumentStatus.QUEUED, DocumentStatus.PROCESSING):
            return ToolResult(
                tool="process_document",
                status="skipped",
                data=self._document_summary(document),
                message="Document already has active processing job.",
            )
        document.status = DocumentStatus.QUEUED
        document.processing_error = None
        document.celery_task_id = None
        await db.commit()
        await db.refresh(document)
        task = self.jobs.enqueue(process_document_task, document.id)
        document.celery_task_id = task.id
        await db.commit()
        await db.refresh(document)
        return ToolResult(
            tool="process_document",
            status="queued",
            data={**self._document_summary(document), "task_id": task.id},
        )

    async def rebuild_document_embeddings(
        self,
        db: AsyncSession,
        *,
        document,
    ) -> ToolResult:
        from app.tasks.embeddings import rebuild_document_embeddings_task

        if document.embedding_status in (EmbeddingStatus.QUEUED, EmbeddingStatus.PROCESSING):
            return ToolResult(
                tool="rebuild_document_embeddings",
                status="skipped",
                data=self._document_summary(document),
                message="Document already has active embedding job.",
            )
        document.embedding_status = EmbeddingStatus.QUEUED
        document.processing_error = None
        await db.commit()
        await db.refresh(document)
        task = self.jobs.enqueue(rebuild_document_embeddings_task, document.id, True)
        document.celery_task_id = task.id
        await db.commit()
        await db.refresh(document)
        return ToolResult(
            tool="rebuild_document_embeddings",
            status="queued",
            data={**self._document_summary(document), "task_id": task.id},
        )

    async def sync_project_embeddings(
        self,
        db: AsyncSession,
        *,
        project,
    ) -> ToolResult:
        from app.tasks.embeddings import sync_project_embeddings_task

        if project.embedding_sync_status in (EmbeddingStatus.QUEUED, EmbeddingStatus.PROCESSING):
            return ToolResult(
                tool="sync_project_embeddings",
                status="skipped",
                data={"project_id": project.id, "task_id": project.embedding_sync_task_id},
                message="Project already has active embedding sync job.",
            )
        project.embedding_sync_status = EmbeddingStatus.QUEUED
        project.embedding_sync_error = None
        project.embedding_sync_task_id = None
        await db.commit()
        await db.refresh(project)
        task = self.jobs.enqueue(sync_project_embeddings_task, project.id)
        project.embedding_sync_task_id = task.id
        await db.commit()
        await db.refresh(project)
        return ToolResult(
            tool="sync_project_embeddings",
            status="queued",
            data={"project_id": project.id, "task_id": task.id, "status": project.embedding_sync_status},
        )

    async def list_workflows(
        self,
        db: AsyncSession,
        *,
        project_id: int,
    ) -> ToolResult:
        workflows = await self.workflows.list_for_project(db, project_id)
        return ToolResult(
            tool="list_workflows",
            status="completed",
            data={"workflows": [{"id": item.id, "name": item.name, "status": item.status} for item in workflows]},
        )

    async def create_workflow(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        name: str,
    ) -> ToolResult:
        workflow = await self.workflows.create(db, Workflow(project_id=project_id, name=name))
        await db.commit()
        await db.refresh(workflow)
        return ToolResult(
            tool="create_workflow",
            status="completed",
            data={"id": workflow.id, "name": workflow.name, "status": workflow.status},
        )

    async def create_workflow_step(
        self,
        db: AsyncSession,
        *,
        workflow_id: int,
        name: str,
        prompt_template: str,
        step_order: int = 1,
        depends_on: list[int] | None = None,
    ) -> ToolResult:
        step = await self.workflow_steps.create(
            db,
            WorkflowStep(
                workflow_id=workflow_id,
                name=name,
                prompt_template=prompt_template,
                step_order=step_order,
                depends_on=depends_on or [],
            ),
        )
        await db.commit()
        await db.refresh(step)
        return ToolResult(
            tool="create_workflow_step",
            status="completed",
            data={"id": step.id, "workflow_id": step.workflow_id, "name": step.name, "step_order": step.step_order},
        )

    async def run_workflow(
        self,
        db: AsyncSession,
        *,
        workflow_id: int,
        user_input: str,
    ) -> ToolResult:
        run = await self.workflow_service.enqueue_run(
            db=db,
            workflow_id=workflow_id,
            user_input=user_input,
            jobs=self.jobs,
        )
        return ToolResult(
            tool="run_workflow",
            status="queued",
            data={"run_id": run.id, "workflow_id": run.workflow_id, "task_id": run.celery_task_id, "status": run.status},
        )

    async def list_workflow_runs(
        self,
        db: AsyncSession,
        *,
        workflow_id: int,
        user_id: int,
    ) -> ToolResult:
        runs = await self.workflow_runs.get_for_workflow(db, workflow_id, user_id)
        return ToolResult(
            tool="list_workflow_runs",
            status="completed",
            data={"runs": [{"id": run.id, "status": run.status, "error": run.error} for run in runs]},
        )

    def _document_summary(self, document) -> dict[str, Any]:
        return {
            "id": document.id,
            "filename": document.filename,
            "status": getattr(document.status, "value", document.status),
            "embedding_status": getattr(document.embedding_status, "value", document.embedding_status),
            "embedding_provider": document.embedding_provider,
            "embedding_model": document.embedding_model,
            "embedding_dimensions": document.embedding_dimensions,
            "embeddings_updated_at": (
                document.embeddings_updated_at.isoformat()
                if getattr(document, "embeddings_updated_at", None)
                else None
            ),
        }
