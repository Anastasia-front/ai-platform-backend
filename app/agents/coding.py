from app.agents.base import BaseAgent
from app.enums.agent import AgentType


class CodingAgent(BaseAgent):

    name: AgentType = AgentType.CODING

    system_prompt = (
        "You are a senior software engineer. "
        "Give clean, production-ready code."
    )