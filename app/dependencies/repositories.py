from app.repositories import (
    AgentRunRepository,
    ChatRepository,
    DocumentRepository,
    MessageRepository,
    ProjectRepository,
    WorkflowEventRepository,
    WorkflowRepository,
    WorkflowRunRepository,
    WorkflowStepRepository,
    WorkflowStepRunRepository,
)


def get_agent_run_repository():
    return AgentRunRepository()

def get_project_repository():
    return ProjectRepository()

def get_chat_repository():
    return ChatRepository()

def get_message_repository():
    return MessageRepository()

def get_workflow_repository():
    return WorkflowRepository()

def get_workflow_run_repository():
    return WorkflowRunRepository()

def get_workflow_step_repository():
    return WorkflowStepRepository()

def get_workflow_step_run_repository():
    return WorkflowStepRunRepository()

def get_workflow_event_repository():
    return WorkflowEventRepository()

def get_document_repository():
    return DocumentRepository()