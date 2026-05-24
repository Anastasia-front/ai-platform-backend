from app.agents.base import BaseAgent


class CodingAgent(BaseAgent):

    name = "coding"

    system_prompt = (
        "You are a senior software engineer. "
        "Give clean, production-ready code."
    )