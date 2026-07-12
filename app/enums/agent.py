from enum import Enum


class AgentRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class AgentType(str, Enum):
    ASSISTANT = "assistant"
    BASE = "base"
    CODING = "coding"
    PROJECT = "project"
    RESEARCH = "research"
