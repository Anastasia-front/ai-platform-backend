from fastapi import Depends

from app.core import settings
from app.dependencies.repositories import get_retrieval_repository
from app.repositories import (
    RetrievalRepository,
    WorkflowRunRepository,
)
from app.services import EmbeddingService, RetrievalService, WorkflowService
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
            dimensions=384,
            model_name=settings.OLLAMA_EMBEDDING_MODEL,
        )

    return _embedding_service


def get_retrieval_service(
    retrieval_repository: RetrievalRepository = Depends(get_retrieval_repository),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> RetrievalService:
    return RetrievalService(
        retrieval_repository=retrieval_repository,
        embedding_service=embedding_service,
    )
