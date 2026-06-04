from app.agents.base import BaseAgent
from app.enums.agent import AgentType


class ResearchAgent(BaseAgent):

    name: AgentType = AgentType.RESEARCH

    system_prompt = (
        "You are a professional research assistant. "
        "Provide structured and analytical answers."
    )