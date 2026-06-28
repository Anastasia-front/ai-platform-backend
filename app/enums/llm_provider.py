from enum import StrEnum


class LLMProvider(StrEnum):
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"
    GROQ = "groq"
    GEMINI = "gemini"