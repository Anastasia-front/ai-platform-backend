from sqlalchemy.ext.asyncio import AsyncSession

from app.core import SIMILARITY_THRESHOLD
from app.prompts import RAGPromptBuilder
from app.services.ai import AIService
from app.services.retrieval import RetrievalService


class RAGService:
    def __init__(
        self,
        retrieval_service: RetrievalService,
        ai_service: AIService,
        prompt_builder: RAGPromptBuilder,
    ) -> None:
        self.retrieval = retrieval_service
        self.ai = ai_service
        self.prompts = prompt_builder

    async def answer(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        user_id: int,
        question: str,
        history: list[dict],
        system_prompt: str,
        top_k: int = 5,
    ) -> tuple[str, list[dict]]:

        retrieved = await self.retrieval.retrieve(
            db=db,
            project_id=project_id,
            user_id=user_id,
            query=question,
            top_k=top_k,
        )

        filtered_results = [
            r for r in retrieved.results if r.score <= SIMILARITY_THRESHOLD
        ]

        context = self.prompts.build_context(filtered_results)

        rag_system_prompt = self.prompts.build_system_prompt(
            base_prompt=system_prompt,
            context=context,
        )

        answer = await self.ai.generate_chat_response(
            messages=history,
            system_prompt=rag_system_prompt,
        )

        sources = [
            {
                "document_name": r.document_name,
                "document_id": r.document_id,
                "chunk_id": r.chunk_id,
                "chunk_index": r.chunk_index,
                "score": r.score,
            }
            for r in retrieved.results
        ]

        return answer, sources
