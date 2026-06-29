from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.dependencies import (
    get_embedding_management_service,
    get_owned_document,
    get_owned_project,
)
from app.models import Document, Project
from app.services.embedding_management import EmbeddingManagementService

router = APIRouter(tags=["Embeddings"])

# Deletes embeddings for:
# current provider + current model + this document
# Then creates them again.

# Use when:
# changed model
# embedding generation failed
# want force refresh
@router.post("/documents/{document_id}/embeddings/rebuild")
async def rebuild_document_embeddings(
    db: AsyncSession = Depends(get_db),
    document: Document = Depends(get_owned_document),
    service: EmbeddingManagementService = Depends(
        get_embedding_management_service
    ),
):
    count = await service.rebuild_document_embeddings(
        db=db,
        document_id=document.id,
    )

    return {
        "status": "completed",
        "document_id": document.id,
        "embeddings_created": count,
    }

# Creates only missing embeddings for:
# current provider + current model + all project chunks

# Use when:
# switching provider
# adding a new embedding model
# existing chunks already exist
# do not want to re-upload/reprocess documents
@router.post("/projects/{project_id}/embeddings/sync")
async def sync_project_embeddings(
    db: AsyncSession = Depends(get_db),
    project: Project = Depends(get_owned_project),
    service: EmbeddingManagementService = Depends(
        get_embedding_management_service
    ),
):
    count = await service.sync_project_embeddings(
        db=db,
        project_id=project.id,
    )

    return {
        "status": "completed",
        "project_id": project.id,
        "embeddings_created": count,
    }