from fastapi import FastAPI

from app.api.router import router

app = FastAPI(
    title="AI Automation Platform",
)

app.include_router(router)