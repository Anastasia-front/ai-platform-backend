from pydantic_settings import BaseSettings, SettingsConfigDict

from app.enums import ChatProvider, EmbeddingProvider


class Settings(BaseSettings):
    DATABASE_URL: str
    
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    JWT_SECRET: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    CHAT_PROVIDER: ChatProvider = ChatProvider.OLLAMA
    EMBEDDING_PROVIDER: EmbeddingProvider = EmbeddingProvider.OLLAMA

    CHAT_BASE_URL: str = "http://localhost:11434"
    EMBEDDING_BASE_URL: str = "http://localhost:11434"

    CHAT_API_KEY: str = ""
    EMBEDDING_API_KEY: str = ""

    CHAT_MODEL: str = "gemma2:2b"
    CHAT_FALLBACK_MODEL: str = "llama3.2:3b"

    EMBEDDING_MODEL: str = "nomic-embed-text"
    EMBEDDING_DIM: int = 768

    STORAGE_PROVIDER: str
    AWS_S3_BUCKET: str = "ai-platform-uploads"
    AWS_REGION: str = "eu-central-1"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
