from app.agents.base import BaseAgent
from app.enums.agent import AgentType


class ResearchAgent(BaseAgent):

    name: AgentType = AgentType.RESEARCH
    agentic = True

    system_prompt = (
        "You are a professional research assistant. "
        "Break complex questions into focused research steps internally. "
        "Use available project documents as primary evidence, compare sources, "
        "and provide structured, analytical answers."
    )
