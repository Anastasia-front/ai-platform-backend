from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import router
from app.services.workflow.recovery import (
    recover_running_workflows,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await recover_running_workflows()
    yield


app = FastAPI(
    title="AI Automation Platform",
    lifespan=lifespan
)

app.include_router(router)