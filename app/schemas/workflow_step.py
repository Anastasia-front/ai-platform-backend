from datetime import datetime

from pydantic import BaseModel


class WorkflowStepCreate(BaseModel):
    step_order: int
    name: str
    prompt_template: str


class WorkflowStepResponse(BaseModel):
    id: int
    workflow_id: int
    step_order: int
    name: str
    prompt_template: str
    created_at: datetime

    class Config:
        from_attributes = True