from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.enums import DocumentStatus, EmbeddingStatus
from app.services.workspace_tools import WorkspaceToolRegistry


def _doc(
    id,
    filename,
    *,
    status=DocumentStatus.INDEXED,
    embedding_status=EmbeddingStatus.COMPLETED,
    provider="gemini",
    model="text-embedding-004",
    dimensions=768,
    text="ready",
):
    return SimpleNamespace(
        id=id,
        filename=filename,
        status=status,
        embedding_status=embedding_status,
        embedding_provider=provider,
        embedding_model=model,
        embedding_dimensions=dimensions,
        embeddings_updated_at=None,
        text=text,
        processing_error=None,
        celery_task_id=None,
    )


@pytest.mark.asyncio
async def test_workspace_tools_classify_embedding_rebuild_need():
    registry = WorkspaceToolRegistry(
        documents=SimpleNamespace(
            list_for_project=AsyncMock(
                return_value=[
                    _doc(1, "current.txt"),
                    _doc(2, "old_model.txt", model="old-model"),
                    _doc(3, "missing.txt", embedding_status=EmbeddingStatus.PENDING, provider=None, model=None, dimensions=None),
                    _doc(4, "processing.txt", embedding_status=EmbeddingStatus.PROCESSING),
                    _doc(5, "uploaded.txt", status=DocumentStatus.UPLOADED, text=None),
                ]
            )
        ),
        workflows=Mock(),
        workflow_steps=Mock(),
        workflow_runs=Mock(),
        workflow_service=Mock(),
        embedding_service=SimpleNamespace(
            provider="gemini",
            model_name="text-embedding-004",
            dimensions=768,
        ),
        jobs=Mock(),
    )

    result = await registry.check_embedding_rebuild_need(AsyncMock(), project_id=10)
    classification = result.data["classification"]

    assert [item["filename"] for item in classification["current"]] == ["current.txt"]
    assert [item["filename"] for item in classification["rebuild_required"]] == ["old_model.txt"]
    assert [item["filename"] for item in classification["unknown_metadata"]] == ["missing.txt"]
    assert [item["filename"] for item in classification["active_jobs"]] == ["processing.txt"]
    assert [item["filename"] for item in classification["not_ready"]] == ["uploaded.txt"]
