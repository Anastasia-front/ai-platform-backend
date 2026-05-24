from app.agents.base import BaseAgent


class AssistantAgent(BaseAgent):

    name = "assistant"

    system_prompt = (
        "You are a helpful AI assistant "
        "inside an AI automation platform."
    )