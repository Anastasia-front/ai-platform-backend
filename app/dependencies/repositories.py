from app.repositories import (
    ChatRepository,
    DocumentRepository,
    MessageRepository,
    ProjectRepository,
    WorkflowEventRepository,
    WorkflowRepository,
    WorkflowRunRepository,
    WorkflowStepRunRepository,
)


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


def get_workflow_step_run_repository():
    return WorkflowStepRunRepository()

def get_workflow_event_repository():
    return WorkflowEventRepository()

def get_document_repository():
    return DocumentRepository()