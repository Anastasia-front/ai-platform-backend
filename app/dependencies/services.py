
from fastapi import Depends

from app.core import settings
from app.dependencies.repositories import (
    get_message_repository,
    get_retrieval_repository,
)
from app.prompts import RAGPromptBuilder
from app.repositories import (
    MessageRepository,
    RetrievalRepository,
    WorkflowRunRepository,
)
from app.services import (
    AIService,
    ChatService,
    EmbeddingManagementService,
    EmbeddingService,
    RAGService,
    RetrievalService,
    WorkflowService,
)
from app.services.storage import (
    LocalStorageService,
    S3StorageService,
    StorageService,
)
from app.services.workflow import DAGEngine, EventBus


def get_workflow_service():

    return WorkflowService(
        runs=WorkflowRunRepository(),
        events=EventBus(),
        engine=DAGEngine(),
    )


# singleton: simpler (one instance for the whole app)
# slightly more efficient
# no downside for a stateless service
# when you swap in a real embedding model, you won't need to change the dependency
# don't put mutable state into services later
_embedding_service = EmbeddingService()


def get_embedding_service() -> EmbeddingService:
    global _embedding_service

    if _embedding_service is None:
        _embedding_service = EmbeddingService(
            dimensions=768,
            model_name=settings.OLLAMA_EMBEDDING_MODEL,
        )

    return _embedding_service


def get_ai_service() -> AIService:
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


def get_chat_service(
    messages: MessageRepository = Depends(get_message_repository),
    rag: RAGService = Depends(get_rag_service),
) -> ChatService:
    return ChatService(
        messages=messages,
        rag=rag,
    )


def get_storage_service() -> StorageService:
    if settings.STORAGE_PROVIDER == "s3":
        return S3StorageService(
            bucket_name=settings.AWS_S3_BUCKET,
            region=settings.AWS_REGION,
        )

    return LocalStorageService()


def get_embedding_management_service(
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> EmbeddingManagementService:
    return EmbeddingManagementService(
        embedding_service=embedding_service,
    )
