from app.enums.agent import AgentType


class BaseAgent:

    name: AgentType = AgentType.BASE

    system_prompt = (
        "You are a helpful AI assistant."
    )