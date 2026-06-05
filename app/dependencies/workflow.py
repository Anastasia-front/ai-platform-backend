from app.repositories import (
    WorkflowRunRepository,
)
from app.services.workflow.dag_engine import DAGEngine
from app.services.workflow.event_bus import EventBus
from app.services.workflow.workflow import WorkflowService


def get_workflow_service():

    return WorkflowService(
        runs=WorkflowRunRepository(),
        events=EventBus(),
        engine=DAGEngine(),
    )