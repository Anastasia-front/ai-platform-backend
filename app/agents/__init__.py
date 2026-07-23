from .assistant import AssistantAgent
from .coding import CodingAgent
from .project import ProjectAgent
from .research import ResearchAgent
from .workspace import WorkspaceAgent

AGENTS = {
    "assistant": AssistantAgent(),
    "project": ProjectAgent(),
    "coding": CodingAgent(),
    "research": ResearchAgent(),
    "workspace": WorkspaceAgent(),
}
