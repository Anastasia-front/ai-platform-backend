from fastapi import APIRouter

from app.api.routes import (
    auth,
    chats,
    messages,
    projects,
    workflow_steps,
    workflows,
)

router = APIRouter()

router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Auth"],
)

router.include_router(
    projects.router,
    tags=["Projects"],
)

router.include_router(
    chats.router,
    tags=["Chats"],
)

router.include_router(
    messages.router,
    tags=["Messages"],
)

router.include_router(
    workflows.router,
    tags=["Workflows"],
)

router.include_router(
    workflow_steps.router,
    tags=["Workflow Steps"],
)