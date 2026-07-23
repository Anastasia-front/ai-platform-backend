from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.dependencies import (
    get_background_job_service,
    get_embedding_job_service,
    get_owned_document,
    get_owned_project,
)
from app.models import Document, Project
from app.services import BackgroundJobService, EmbeddingJobService

router = APIRouter(tags=["Embeddings"])

# -------------------------------------------------
# RUN DOCUMENT EMBEDDINGS REBUILD
# -------------------------------------------------
@router.post(
    "/documents/{document_id}/embeddings/rebuild",
    status_code=status.HTTP_202_ACCEPTED,
)
async def rebuild_document_embeddings(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    document: Document = Depends(get_owned_document),
    embedding_jobs: EmbeddingJobService = Depends(get_embedding_job_service),
):
    return await embedding_jobs.rebuild_document(
        db=db,
        document=document,
        background_tasks=background_tasks,
    )

# -------------------------------------------------
# RUN PROJECT EMBEDDINGS SYNC
# -------------------------------------------------
@router.post(
    "/projects/{project_id}/embeddings/sync",
    status_code=status.HTTP_202_ACCEPTED,
)
async def sync_project_embeddings(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    project: Project = Depends(get_owned_project),
    embedding_jobs: EmbeddingJobService = Depends(get_embedding_job_service),
):
    return await embedding_jobs.sync_project(
        db=db,
        project=project,
        background_tasks=background_tasks,
    )

# -------------------------------------------------
# DOCUMENT EMBEDDINGS REBUILD CANCEL
# -------------------------------------------------
@router.post(
    "/documents/{document_id}/embeddings/rebuild/cancel",
    status_code=status.HTTP_202_ACCEPTED,
)
async def cancel_document_embedding_rebuild(
    db: AsyncSession = Depends(get_db),
    document: Document = Depends(get_owned_document),
    jobs: BackgroundJobService = Depends(get_background_job_service),
    embedding_jobs: EmbeddingJobService = Depends(get_embedding_job_service),
):
    return await embedding_jobs.cancel_document_rebuild(
        db=db,
        document=document,
        jobs=jobs,
    )

# -------------------------------------------------
# DOCUMENT EMBEDDINGS REBUILD RESUME
# -------------------------------------------------
@router.post(
    "/documents/{document_id}/embeddings/rebuild/resume",
    status_code=status.HTTP_202_ACCEPTED,
)
async def resume_document_embedding_rebuild(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    document: Document = Depends(get_owned_document),
    embedding_jobs: EmbeddingJobService = Depends(get_embedding_job_service),
):
    return await embedding_jobs.resume_document_rebuild(
        db=db,
        document=document,
        background_tasks=background_tasks,
    )


# -------------------------------------------------
# DOCUMENT EMBEDDINGS REBUILD RETRY
# -------------------------------------------------
@router.post(
    "/documents/{document_id}/embeddings/rebuild/retry",
    status_code=status.HTTP_202_ACCEPTED,
)
async def retry_document_embedding_rebuild(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    document: Document = Depends(get_owned_document),
    embedding_jobs: EmbeddingJobService = Depends(get_embedding_job_service),
):
    return await embedding_jobs.retry_document_rebuild(
        db=db,
        document=document,
        background_tasks=background_tasks,
    )


# -------------------------------------------------
# PROJECT EMBEDDINGS SYNC CANCEL
# -------------------------------------------------
@router.post(
    "/projects/{project_id}/embeddings/sync/cancel",
    status_code=status.HTTP_202_ACCEPTED,
)
async def cancel_project_embedding_sync(
    db: AsyncSession = Depends(get_db),
    project: Project = Depends(get_owned_project),
    jobs: BackgroundJobService = Depends(get_background_job_service),
    embedding_jobs: EmbeddingJobService = Depends(get_embedding_job_service),
):
    return await embedding_jobs.cancel_project_sync(
        db=db,
        project=project,
        jobs=jobs,
    )


# -------------------------------------------------
# PROJECT EMBEDDINGS SYNC RESUME
# -------------------------------------------------
@router.post(
    "/projects/{project_id}/embeddings/sync/resume",
    status_code=status.HTTP_202_ACCEPTED,
)
async def resume_project_embedding_sync(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    project: Project = Depends(get_owned_project),
    embedding_jobs: EmbeddingJobService = Depends(get_embedding_job_service),
):
    return await embedding_jobs.resume_project_sync(
        db=db,
        project=project,
        background_tasks=background_tasks,
    )


# -------------------------------------------------
# PROJECT EMBEDDINGS SYNC RETRY
# -------------------------------------------------
@router.post(
    "/projects/{project_id}/embeddings/sync/retry",
    status_code=status.HTTP_202_ACCEPTED,
)
async def retry_project_embedding_sync(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    project: Project = Depends(get_owned_project),
    embedding_jobs: EmbeddingJobService = Depends(get_embedding_job_service),
):
    return await embedding_jobs.retry_project_sync(
        db=db,
        project=project,
        background_tasks=background_tasks,
    )

# -------------------------------------------------
# PROJECT EMBEDDINGS SYNC STATUS
# -------------------------------------------------
@router.get("/projects/{project_id}/embeddings/sync")
async def get_project_embedding_sync_status(
    project: Project = Depends(get_owned_project),
    embedding_jobs: EmbeddingJobService = Depends(get_embedding_job_service),
):
    return embedding_jobs.project_sync_status(project)
