from app.enums.agent import AgentType


class BaseAgent:

    name: AgentType = AgentType.BASE

    agentic: bool = False
    uses_rag: bool = False

    system_prompt = (
        "You are a helpful AI assistant."
    )
