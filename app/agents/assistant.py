from app.agents.base import BaseAgent
from app.enums.agent import AgentType


class AssistantAgent(BaseAgent):

    name: AgentType = AgentType.ASSISTANT

    system_prompt = (
        "You are a helpful AI assistant "
        "inside an AI automation platform."
    )