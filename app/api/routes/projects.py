from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.dependencies import (
    get_current_user,
    get_owned_project,
    get_project_repository,
    get_retrieval_service,
)
from app.models import Project, User
from app.repositories import ProjectRepository
from app.schemas import (
    ProjectCreate,
    ProjectResponse,
    RetrievalRequest,
    RetrievalResponse,
)
from app.services import RetrievalService

router = APIRouter()

# -------------------------------------------------
# CREATE PROJECT
# -------------------------------------------------
@router.post(
    "/", 
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    projects: ProjectRepository = Depends(
        get_project_repository
    ),
):
    project = Project(
        name=payload.name,
        description=payload.description,
    )

    await projects.create(
        db=db,
        project=project,
        user_id=user.id
    )
    await db.commit()
    await db.refresh(project)

    return project

# -------------------------------------------------
#  GET SINGLE PROJECT
# -------------------------------------------------
@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project: Project = Depends(get_owned_project),
):
    return project

# -------------------------------------------------
#  GET PROJECTS
# -------------------------------------------------
@router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    projects: ProjectRepository = Depends(
        get_project_repository
    )
):
    return await projects.list_for_user(
        db,
        user.id,
    )   

# -------------------------------------------------
#  RETRIEVE PROJECTS
# -------------------------------------------------
@router.post(
    "/{project_id}/retrieve",
    response_model=RetrievalResponse,
)
async def retrieve(
    request: RetrievalRequest,
    db: AsyncSession = Depends(get_db),
    project: Project = Depends(get_owned_project),
    current_user: User = Depends(get_current_user),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
):
    return await retrieval_service.retrieve(
        db=db,
        project_id=project.id,
        user_id=current_user.id,
        query=request.query,
        top_k=request.top_k,
    )

# -------------------------------------------------
# DELETE PROJECT
# -------------------------------------------------
@router.delete(
    "/{project_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    db: AsyncSession = Depends(get_db),
    project: Project = Depends(get_owned_project),
    projects: ProjectRepository = Depends(
        get_project_repository
    ),
):
    await projects.delete(
    db,
    project,
)
    await db.commit()