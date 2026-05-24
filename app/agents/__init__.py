from app.agents.assistant import AssistantAgent
from app.agents.coding import CodingAgent
from app.agents.research import ResearchAgent

AGENTS = {
    "assistant": AssistantAgent(),
    "coding": CodingAgent(),
    "research": ResearchAgent(),
}