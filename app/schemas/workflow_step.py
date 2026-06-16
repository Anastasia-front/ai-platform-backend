from datetime import datetime

from pydantic import BaseModel


class WorkflowStepCreate(BaseModel):
    step_order: int
    name: str
    prompt_template: str

    depends_on: list[int] | None = []
    condition: str | None = None


class WorkflowStepResponse(BaseModel):
    id: int
    workflow_id: int
    step_order: int
    name: str
    prompt_template: str

    depends_on: list[int] | None = []
    condition: str | None = None

    created_at: datetime

    # model_config = ConfigDict(
    #     from_attributes=True
    # )

    class Config:
        from_attributes = True