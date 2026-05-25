from .assistant import AssistantAgent
from .coding import CodingAgent
from .research import ResearchAgent

AGENTS = {
    "assistant": AssistantAgent(),
    "coding": CodingAgent(),
    "research": ResearchAgent(),
}