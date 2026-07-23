from app.agents.base import BaseAgent
from app.enums.agent import AgentType


class WorkspaceAgent(BaseAgent):

    name: AgentType = AgentType.WORKSPACE
    agentic = True
    uses_rag = True
    workspace = True

    system_prompt = (
        "You are the Workspace Agent for an AI automation platform. "
        "Inspect project context, use platform tools for operational tasks, "
        "reuse existing services, and report concise execution results. "
        "Never ask the user to manually inspect resources when a safe platform "
        "tool can do it."
    )
