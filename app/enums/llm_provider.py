from enum import StrEnum


class ChatProvider(StrEnum):
    OLLAMA = "ollama"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    GROQ = "groq"


class EmbeddingProvider(StrEnum):
    OLLAMA = "ollama"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"