from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import AGENTS
from app.models import Chat, Message
from app.models.user import User
from app.repositories import MessageRepository
from app.services.rag import RAGService


class ChatService:
    def __init__(
        self,
        messages: MessageRepository,
        rag: RAGService,
    ) -> None:
        self.messages = messages
        self.rag = rag

    async def create_message(
        self,
        db: AsyncSession,
        *,
        chat: Chat,
        user: User,
        content: str,
        agent_name: str | None = None,
    ) -> tuple[Message, Message]:

        # ---------------------------------
        # Save user message
        # ---------------------------------

        user_message = Message(
            chat_id=chat.id,
            role="user",
            content=content,
        )

        await self.messages.create(
            db,
            user_message,
        )

        await db.flush()

        # ---------------------------------
        # Conversation history
        # ---------------------------------

        history = await self.messages.list_for_chat(
            db,
            chat.id,
        )

        ollama_messages = [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in history
        ]

        # ---------------------------------
        # Agent
        # ---------------------------------

        selected_agent_name = agent_name or chat.agent_name
        agent = AGENTS.get(selected_agent_name)

        if agent is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid agent",
            )

        # ---------------------------------
        # Generate answer using RAG
        # ---------------------------------

        answer, sources = await self.rag.answer(
            db=db,
            project_id=chat.project_id,
            user_id=user.id,
            question=content,
            history=ollama_messages,
            system_prompt=agent.system_prompt,
        )

        # ---------------------------------
        # Save assistant message
        # ---------------------------------

        assistant_message = Message(
            chat_id=chat.id,
            role="assistant",
            content=answer,
            sources=sources,
        )

        await self.messages.create(
            db,
            assistant_message,
        )

        await db.commit()

        await db.refresh(user_message)
        await db.refresh(assistant_message)

        return user_message, assistant_message


# answer, sources = await self.rag.answer(...)

# That means RAGService should become responsible for the complete RAG pipeline:

# question
#     ↓
# embed query
#     ↓
# retrieve chunks
#     ↓
# build context
#     ↓
# call AIService
#     ↓
# return answer + sources

# So your route doesn't know RAG exists, and ChatService doesn't know how prompts are constructed. Each layer has a single responsibility:

# Route → HTTP.
# ChatService → orchestrates the chat workflow.
# RAGService → retrieval, context construction, citations, and LLM invocation.
# AIService → communicates with Ollama only.

# This separation will make it much easier to add streaming responses,
# multiple retrieval strategies, or workflow-specific context later without changing the route or ChatService
