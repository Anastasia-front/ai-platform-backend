
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db, settings
from app.dependencies.repositories import (
    get_agent_run_repository,
    get_chat_repository,
    get_document_chunk_repository,
    get_document_repository,
    get_message_repository,
    get_project_repository,
    get_retrieval_repository,
    get_workflow_repository,
    get_workflow_run_repository,
    get_workflow_step_repository,
)
from app.prompts import RAGPromptBuilder
from app.repositories import (
    AgentRunRepository,
    ChatRepository,
    DocumentChunkRepository,
    DocumentRepository,
    MessageRepository,
    ProjectRepository,
    RetrievalRepository,
    WorkflowRepository,
    WorkflowRunRepository,
    WorkflowStepRepository,
)
from app.services import (
    AgentRunUpdateService,
    AgentService,
    AIService,
    BackgroundJobService,
    ChatService,
    ChatUpdateService,
    DocumentService,
    EmbeddingJobService,
    EmbeddingManagementService,
    EmbeddingService,
    HealthService,
    ProjectUpdateService,
    RAGService,
    RetrievalService,
    WorkflowService,
    WorkflowStepUpdateService,
    WorkflowUpdateService,
    WorkspaceToolRegistry,
)
from app.services.provider_config import provider_config
from app.services.storage import (
    LocalStorageService,
    S3StorageService,
    StorageService,
)
from app.services.workflow import DAGEngine, EventBus


def get_workflow_service():
    events = EventBus()

    return WorkflowService(
        runs=WorkflowRunRepository(),
        events=events,
        engine=DAGEngine(events=events),
    )


def get_project_update_service(
    projects: ProjectRepository = Depends(get_project_repository),
) -> ProjectUpdateService:
    return ProjectUpdateService(projects=projects)


def get_chat_update_service(
    chats: ChatRepository = Depends(get_chat_repository),
) -> ChatUpdateService:
    return ChatUpdateService(chats=chats)


def get_workflow_update_service(
    workflows: WorkflowRepository = Depends(get_workflow_repository),
) -> WorkflowUpdateService:
    return WorkflowUpdateService(workflows=workflows)


def get_workflow_step_update_service(
    steps: WorkflowStepRepository = Depends(get_workflow_step_repository),
) -> WorkflowStepUpdateService:
    return WorkflowStepUpdateService(steps=steps)


def get_agent_run_update_service(
    agent_runs: AgentRunRepository = Depends(get_agent_run_repository),
) -> AgentRunUpdateService:
    return AgentRunUpdateService(agent_runs=agent_runs)


def get_background_job_service() -> BackgroundJobService:
    return BackgroundJobService()


def get_health_service() -> HealthService:
    return HealthService()


async def get_embedding_service(
    db: AsyncSession = Depends(get_db),
) -> EmbeddingService:
    await provider_config.load_from_db(db)
    return EmbeddingService()


async def get_ai_service(
    db: AsyncSession = Depends(get_db),
) -> AIService:
    await provider_config.load_from_db(db)
    return AIService()


def get_retrieval_service(
    retrievals: RetrievalRepository = Depends(get_retrieval_repository),
    embeddings: EmbeddingService = Depends(get_embedding_service),
) -> RetrievalService:
    return RetrievalService(
        embedding_service=embeddings,
        retrieval_repository=retrievals,
    )


def get_rag_prompt_builder() -> RAGPromptBuilder:
    return RAGPromptBuilder()


def get_rag_service(
    retrieval: RetrievalService = Depends(get_retrieval_service),
    ai: AIService = Depends(get_ai_service),
    prompts: RAGPromptBuilder = Depends(get_rag_prompt_builder),
) -> RAGService:
    return RAGService(
        retrieval_service=retrieval,
        ai_service=ai,
        prompt_builder=prompts,
    )


def get_workspace_tool_registry(
    documents: DocumentRepository = Depends(get_document_repository),
    workflows: WorkflowRepository = Depends(get_workflow_repository),
    workflow_steps: WorkflowStepRepository = Depends(get_workflow_step_repository),
    workflow_runs: WorkflowRunRepository = Depends(get_workflow_run_repository),
    workflow_service: WorkflowService = Depends(get_workflow_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    jobs: BackgroundJobService = Depends(get_background_job_service),
) -> WorkspaceToolRegistry:
    return WorkspaceToolRegistry(
        documents=documents,
        workflows=workflows,
        workflow_steps=workflow_steps,
        workflow_runs=workflow_runs,
        workflow_service=workflow_service,
        embedding_service=embedding_service,
        jobs=jobs,
    )


def get_agent_service(
    ai: AIService = Depends(get_ai_service),
    rag: RAGService = Depends(get_rag_service),
    documents: DocumentRepository = Depends(get_document_repository),
    workspace_tools: WorkspaceToolRegistry = Depends(get_workspace_tool_registry),
    prompts: RAGPromptBuilder = Depends(get_rag_prompt_builder),
) -> AgentService:
    return AgentService(
        ai=ai,
        rag=rag,
        documents=documents,
        workspace_tools=workspace_tools,
        prompts=prompts,
    )


def get_chat_service(
    messages: MessageRepository = Depends(get_message_repository),
    rag: RAGService = Depends(get_rag_service),
    ai: AIService = Depends(get_ai_service),
    agent_service: AgentService = Depends(get_agent_service),
) -> ChatService:
    return ChatService(
        messages=messages,
        rag=rag,
        ai=ai,
        agent_service=agent_service,
    )


def get_storage_service() -> StorageService:
    if settings.STORAGE_PROVIDER == "s3":
        return S3StorageService(
            bucket_name=settings.AWS_S3_BUCKET,
            region=settings.AWS_REGION,
        )

    return LocalStorageService()


def get_document_service(
    storage: StorageService = Depends(get_storage_service),
    documents: DocumentRepository = Depends(get_document_repository),
    chunks: DocumentChunkRepository = Depends(get_document_chunk_repository),
) -> DocumentService:
    return DocumentService(
        storage=storage,
        documents=documents,
        chunks=chunks,
    )


def get_embedding_management_service(
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> EmbeddingManagementService:
    return EmbeddingManagementService(
        embedding_service=embedding_service,
    )


def get_embedding_job_service() -> EmbeddingJobService:
    return EmbeddingJobService()
