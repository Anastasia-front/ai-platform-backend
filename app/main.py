from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import router
from app.core import AsyncSessionLocal
from app.services.provider_config import provider_config
from app.services.workflow.recovery import (
    recover_running_workflows,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSessionLocal() as db:
        await provider_config.seed_defaults(db)
        await provider_config.load_from_db(db)
    await recover_running_workflows()
    yield


app = FastAPI(title="AI Automation Platform", lifespan=lifespan)

app.include_router(router)
