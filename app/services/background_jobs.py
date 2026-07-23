from typing import Any

from celery import Task
from fastapi import HTTPException, status
from kombu.exceptions import OperationalError

from app.core.celery_app import celery_app


class BackgroundJobService:
    def enqueue(self, task: Task, *args: Any, **kwargs: Any):
        try:
            return task.delay(*args, **kwargs)
        except OperationalError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Background job queue is unavailable. "
                    "Please start Redis/Celery and try again."
                ),
            ) from exc

    def revoke(self, task_id: str, terminate: bool = True) -> None:
        try:
            celery_app.control.revoke(task_id, terminate=terminate)
        except OperationalError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Background job queue is unavailable. "
                    "The run was marked canceled, but the worker could not be notified."
                ),
            ) from exc
