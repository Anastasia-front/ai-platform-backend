from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.dependencies import get_current_user, get_owned_project, get_project_repository
from app.repositories import ProjectRepository
from app.schemas import ProjectCreate, ProjectResponse

router = APIRouter()

# -------------------------------------------------
# CREATE PROJECT
# -------------------------------------------------
@router.post("/", response_model=ProjectResponse)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
    projects: ProjectRepository = Depends(
        get_project_repository
    ),
):
    project = await projects.create(
        db=db,
        **payload.model_dump(),
        user_id=user.id,
    )
    await db.commit()
    await db.refresh(project)

    return project

# -------------------------------------------------
#  GET SINGLE PROJECT
# -------------------------------------------------
@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project = Depends(get_owned_project),
):
    return project

# -------------------------------------------------
#  GET PROJECTS
# -------------------------------------------------
@router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
    projects: ProjectRepository = Depends(
        get_project_repository
    )
):
    return await projects.list_for_user(
        db,
        user.id,
    )   

# -------------------------------------------------
# DELETE PROJECT
# -------------------------------------------------
@router.delete("/{project_id}")
async def delete_project(
    db: AsyncSession = Depends(get_db),
    project = Depends(get_owned_project),
    projects: ProjectRepository = Depends(
        get_project_repository
    ),
):
    await projects.delete(
    db,
    project,
)
    await db.commit()

    return {
        "message": "Project deleted",
    }