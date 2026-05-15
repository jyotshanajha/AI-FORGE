from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "amzur-ai-chat"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = ""
    JWT_EXPIRE_MINUTES: int = 480
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"

    # Database
    DATABASE_URL: str = ""

    # LiteLLM
    LITELLM_PROXY_URL: str = ""
    LITELLM_API_KEY: str = ""
    LITELLM_USER_ID: Optional[str] = None
    LLM_MODEL: str = "gemini/gemini-2.5-flash"
    LITELLM_EMBEDDING_MODEL: str = "text-embedding-3-large"
    IMAGE_GEN_MODEL: str = "gemini/imagen-4.0-fast-generate-001"

    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None

    # File and vector store
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    GOOGLE_SERVICE_ACCOUNT_JSON: Optional[str] = None
    MAX_UPLOAD_MB: int = 20
    UPLOAD_DIR: str = "./uploads"
    CHAT_MEMORY_CONVERSATION_LIMIT: int = 5
    ALLOWED_ATTACHMENT_MIME_TYPES: str = (
        "image/jpeg,image/png,image/webp,image/gif,"
        "video/mp4,video/webm,video/quicktime,"
        "text/plain,text/csv,text/markdown,application/json,"
        "application/pdf,application/x-tex,text/x-tex,application/octet-stream,"
        "application/vnd.ms-excel,"
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,"
        "text/x-python,application/javascript,text/javascript"
    )

    @property
    def allowed_attachment_mime_types(self) -> set[str]:
        values = [item.strip().lower() for item in self.ALLOWED_ATTACHMENT_MIME_TYPES.split(",")]
        return {item for item in values if item}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
