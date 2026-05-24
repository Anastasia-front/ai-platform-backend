from app.agents.base import BaseAgent


class ResearchAgent(BaseAgent):

    name = "research"

    system_prompt = (
        "You are a professional research assistant. "
        "Provide structured and analytical answers."
    )