from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    # Database (Supabase)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    # Optional direct Postgres (for local dev or tooling)
    DATABASE_URL: Optional[str] = None

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # LLM
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash-001"
    GEMINI_EMBEDDING_MODEL: str = "text-embedding-004"
    VERTEX_PROJECT_ID: Optional[str] = None
    VERTEX_LOCATION: str = "us-central1"
    VERTEX_MODEL: str = "google/gemini-2.0-flash-lite-001"
    LLM_PROVIDER: str = "openai"  # openai | anthropic | gemini | vertex

    # Performance / timeouts
    # Upper bound for a single LLM response generation (seconds).
    LLM_TIMEOUT_SECONDS: float = 20.0
    # Upper bound for context/memory retrieval before falling back to empty context (seconds).
    CONTEXT_RETRIEVAL_TIMEOUT_SECONDS: float = 1.5
    # Upper bound for optional contradiction detection (seconds).
    CONFLICT_DETECTION_TIMEOUT_SECONDS: float = 2.0
    # Run conflict detection inline (slower) vs best-effort background.
    ENABLE_INLINE_CONFLICT_DETECTION: bool = False
    # If Celery isn't available, run reflection inline (very slow). Keep disabled for snappy chat.
    ENABLE_REFLECTION_SYNC_FALLBACK: bool = False

    # App
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week
    RATE_LIMIT_PER_MINUTE: int = 60
    LOGIN_ATTEMPT_LIMIT: int = 5
    LOGIN_ATTEMPT_WINDOW_SECONDS: int = 900
    AUDIT_RETENTION_DAYS: int = 90
    AUDIT_STORE_PII: bool = False

    # Encryption
    ENCRYPTION_KEY: Optional[str] = None

    # Tool sandbox
    TOOL_SANDBOX_URL: Optional[str] = None

    class Config:
        env_file = str(_ENV_FILE)


settings = Settings()
