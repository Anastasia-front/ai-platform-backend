from app.agents.base import BaseAgent
from app.enums.agent import AgentType


class ProjectAgent(BaseAgent):

    name: AgentType = AgentType.PROJECT
    agentic = True
    uses_rag = True

    system_prompt = (
        "You answer questions using uploaded and indexed project documents. "
        "Use retrieved context as the source of truth and cite evidence."
    )
