from app.agents.base import BaseAgent
from app.enums.agent import AgentType


class CodingAgent(BaseAgent):

    name: AgentType = AgentType.CODING
    agentic = True

    system_prompt = (
        "You are a senior software engineer. "
        "Reason through implementation constraints internally, use project "
        "documents when available, and give clean, production-ready code."
    )
