from collections import defaultdict

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
            r
            for r in retrieved.results
            if r.score <= SIMILARITY_THRESHOLD
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

        sources = self._build_sources(filtered_results)

        return answer, sources

    def _build_sources(
        self,
        chunks,
    ) -> list[dict]:

        grouped = defaultdict(list)

        for chunk in chunks:
            grouped[
                (
                    chunk.document_id,
                    chunk.document_name,
                )
            ].append(chunk)

        sources = []

        for (
            document_id,
            document_name,
        ), matches in grouped.items():

            sources.append(
                {
                    "document_id": document_id,
                    "document_name": document_name,
                    "matches": len(matches),
                    "best_score": min(m.score for m in matches),
                }
            )

        return sorted(
            sources,
            key=lambda s: s["best_score"],
        )


# The flow is now:

# Retrieved chunks
#         ↓
# Threshold filter
#         ↓
# filtered_results
#         ↓
# Context builder
#         ↓
# LLM answer

# filtered_results
#         ↓
# _build_sources()
#         ↓
# deduplicated documents
#         ↓
# frontend citations