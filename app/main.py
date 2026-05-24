from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.chats import router as chats_router
from app.api.routes.documents import router as documents_router
from app.api.routes.messages import router as messages_router
from app.api.routes.projects import router as projects_router
from app.api.routes.workflows import router as workflows_router

app = FastAPI(
    title="AI Automation Platform",
)


app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Auth"],
)

app.include_router(
    projects_router,
    prefix="/projects",
    tags=["Projects"],
)

app.include_router(
    chats_router,
    tags=["Chats"],
)

app.include_router(
    messages_router,
    tags=["Messages"],
)

app.include_router(
    documents_router,
    tags=["Documents"],
)

app.include_router(
    workflows_router,
    tags=["Workflows"],
)