from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

        # You return from route/service:
                # return project
        # where project is a SQLAlchemy model object.

        # FastAPI → Pydantic must be able to read ORM attributes:
                # project.id
                # project.name

        # from_attributes = True enables ORM mode in Pydantic v2.

        # Without this, you usually get errors like:
                # Input must be a valid dictionary
        # or:
                # Unable to serialize SQLAlchemy object