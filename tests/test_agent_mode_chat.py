from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.chat import ChatService


@pytest.mark.asyncio
async def test_assistant_chat_uses_plain_ai_path():
    messages = AsyncMock()
    rag = SimpleNamespace(
        answer=AsyncMock(return_value=("standard answer", [])),
    )
    ai = SimpleNamespace(generate_chat_response=AsyncMock(return_value="plain answer"))
    agent_service = SimpleNamespace(run=AsyncMock(return_value=("agent answer", [])))
    chat = SimpleNamespace(id=1, project_id=10, agent_name="assistant")
    user = SimpleNamespace(id=7)
    history = [
        SimpleNamespace(role="user", content="Hello"),
        SimpleNamespace(role="assistant", content="Hi"),
        SimpleNamespace(role="user", content="What changed?"),
    ]
    messages.list_for_chat.return_value = history
    messages.commit_pair = AsyncMock(side_effect=lambda db, first, second: (first, second))

    await ChatService(
        messages=messages,
        rag=rag,
        ai=ai,
        agent_service=agent_service,
    ).create_message(
        db=AsyncMock(),
        chat=chat,
        user=user,
        content="What changed?",
    )

    ai.generate_chat_response.assert_awaited_once()
    rag.answer.assert_not_awaited()
    agent_service.run.assert_not_awaited()


@pytest.mark.asyncio
async def test_project_chat_uses_agent_orchestrator_with_project_and_history():
    messages = AsyncMock()
    rag = SimpleNamespace(
        answer=AsyncMock(return_value=("rag answer", [])),
    )
    ai = SimpleNamespace(generate_chat_response=AsyncMock(return_value="plain answer"))
    agent_service = SimpleNamespace(run=AsyncMock(return_value=("agent answer", [])))
    chat = SimpleNamespace(id=1, project_id=10, agent_name="project")
    user = SimpleNamespace(id=7)
    history = [
        SimpleNamespace(role="user", content="Summarize uploaded docs"),
    ]
    messages.list_for_chat.return_value = history
    messages.commit_pair = AsyncMock(side_effect=lambda db, first, second: (first, second))

    await ChatService(
        messages=messages,
        rag=rag,
        ai=ai,
        agent_service=agent_service,
    ).create_message(
        db=AsyncMock(),
        chat=chat,
        user=user,
        content="Summarize uploaded docs",
    )

    rag.answer.assert_not_awaited()
    ai.generate_chat_response.assert_not_awaited()
    agent_service.run.assert_awaited_once()


@pytest.mark.asyncio
async def test_agent_mode_uses_agentic_rag_with_project_and_history():
    messages = AsyncMock()
    rag = SimpleNamespace(
        answer=AsyncMock(return_value=("standard answer", [])),
    )
    ai = SimpleNamespace(generate_chat_response=AsyncMock(return_value="plain answer"))
    agent_service = SimpleNamespace(run=AsyncMock(return_value=("agent answer", [])))
    chat = SimpleNamespace(id=1, project_id=10, agent_name="research")
    user = SimpleNamespace(id=7)
    history = [
        SimpleNamespace(role="user", content="Summarize the uploaded report"),
    ]
    messages.list_for_chat.return_value = history
    messages.commit_pair = AsyncMock(side_effect=lambda db, first, second: (first, second))

    await ChatService(
        messages=messages,
        rag=rag,
        ai=ai,
        agent_service=agent_service,
    ).create_message(
        db=AsyncMock(),
        chat=chat,
        user=user,
        content="Summarize the uploaded report",
    )

    rag.answer.assert_not_awaited()
    ai.generate_chat_response.assert_not_awaited()
    agent_service.run.assert_awaited_once()
    kwargs = agent_service.run.await_args.kwargs
    assert kwargs["project_id"] == 10
    assert kwargs["user_id"] == 7
    assert kwargs["history"] == [
        {
            "role": "user",
            "content": "Summarize the uploaded report",
        }
    ]
