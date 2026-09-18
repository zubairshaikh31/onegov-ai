"""
Application configuration.
All settings are loaded from environment variables (via .env in development).
Pydantic Settings provides automatic type coercion and validation.
"""

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, EmailStr, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../backend/.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────────
    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_NAME: str = "OneGov AI"
    APP_VERSION: str = "1.0.0"
    APP_DEBUG: bool = False
    APP_SECRET_KEY: str = Field("dev_secret_key_change_in_production_32chars_minimum", min_length=32)
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # ── Server ─────────────────────────────────────────────────────────────
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # ── Database ───────────────────────────────────────────────────────────
    DATABASE_URL: str = Field(
        "postgresql+asyncpg://onegov:onegov_secret@postgres:5432/onegov_ai",
        pattern=r"^postgresql\+asyncpg://",
    )
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False

    # ── Redis ──────────────────────────────────────────────────────────────
    REDIS_URL: str = Field(
        "redis://:redis_secret@redis:6379/0",
        pattern=r"^(redis|mock)://",
    )
    REDIS_MAX_CONNECTIONS: int = 20

    # ── JWT ────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = Field("dev_jwt_secret_change_in_production_32chars_min", min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── OTP ────────────────────────────────────────────────────────────────
    OTP_EXPIRE_MINUTES: int = 10
    OTP_MAX_ATTEMPTS: int = 5
    OTP_LENGTH: int = 6
    # Echo OTPs only in non-production local dev. NEVER enabled in production.
    ECHO_DEV_OTP: bool = True

    # ── Account Security ───────────────────────────────────────────────────
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 30

    # ── Email ──────────────────────────────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM_NAME: str = "OneGov AI"
    EMAIL_FROM_ADDRESS: str = "noreply@onegov.ai"

    # ── Google OAuth ───────────────────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # ── Twilio / SMS ───────────────────────────────────────────────────────
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # ── LLM / AI ───────────────────────────────────────────────────────────
    LLM_PROVIDER: Literal["ollama", "openai", "gemini", "groq", "claude", "nvidia"] = "ollama"
    LLM_FALLBACK_PROVIDER: Literal["ollama", "openai", "gemini", "groq", "claude", "nvidia", "none"] = "none"
    LLM_TIMEOUT_SECONDS: int = 120
    LLM_MAX_RETRIES: int = 2
    LLM_MAX_TOKENS: int = 1200
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.2"
    EMBEDDING_MODEL: str = "nomic-embed-text"
    EMBEDDING_DIM: int = 768
    EMBEDDING_BATCH_SIZE: int = 16
    EMBEDDING_PROVIDER: str = ""  # falls back to LLM_PROVIDER
    USE_PGVECTOR: bool = True
    KNOWLEDGE_VERSION: str = "v2-2026"
    KNOWLEDGE_BASE_PATH: str = ""  # custom path override for the knowledge base
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    NVIDIA_API_KEY: str = ""
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_MODEL: str = "nvidia/nemotron-3.5-lightning-30b-a3b"

    # ── Logging ────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: Literal["json", "text"] = "json"

    # ── Computed fields ────────────────────────────────────────────────────
    @computed_field  # type: ignore[misc]
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @computed_field  # type: ignore[misc]
    @property
    def access_token_expire_seconds(self) -> int:
        return self.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    @computed_field  # type: ignore[misc]
    @property
    def refresh_token_expire_seconds(self) -> int:
        return self.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance.
    Use this everywhere instead of instantiating Settings() directly.
    The @lru_cache ensures we only read .env once per process.
    """
    return Settings()  # type: ignore[call-arg]


# Module-level shortcut — import `settings` directly in other modules
settings: Settings = get_settings()
