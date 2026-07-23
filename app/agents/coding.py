from app.agents.base import BaseAgent
from app.enums.agent import AgentType


class CodingAgent(BaseAgent):

    name: AgentType = AgentType.CODING
    agentic = True
    workspace = True

    system_prompt = (
        "You are the legacy Coding Agent. Behave as Workspace Agent for "
        "backward compatibility with existing chats."
    )
