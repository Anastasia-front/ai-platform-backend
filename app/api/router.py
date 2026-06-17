from fastapi import APIRouter

from app.api.routes import (
    agent_runs,
    auth,
    chats,
    documents,
    messages,
    projects,
    workflow_runs,
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
    prefix="/projects",
    tags=["Projects"],
)

router.include_router(
    chats.router,
    tags=["Chats"],
)

router.include_router(
    messages.router,
    prefix="/chats",
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

router.include_router(
    workflow_runs.router,
    tags=["Workflow Runs"],
)

router.include_router(
    agent_runs.router,
    tags=["Agent Runs"],
)

router.include_router(
    documents.router,
    prefix="/projects",
    tags=["Documents"],
)