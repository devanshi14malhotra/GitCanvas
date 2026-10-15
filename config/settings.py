"""
Central configuration from environment (.env / process env).
"""

from __future__ import annotations
from utils.logger import setup_logger
from functools import lru_cache
from typing import Optional
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = setup_logger(__name__)

def _secret_plain(secret: Optional[SecretStr]) -> Optional[str]:
    if secret is None:
        return None
    v = secret.get_secret_value().strip()
    return v or None


class GitCanvasSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    github_token: Optional[SecretStr] = Field(default=None)
    openai_api_key: Optional[SecretStr] = Field(default=None)
    gemini_api_key: Optional[SecretStr] = Field(default=None)
    
    # Redis caching configuration
    cache_backend: str = Field(default="local", description="Cache backend: 'local' or 'redis'")
    redis_url: Optional[str] = Field(default=None, description="Redis connection URL (e.g., redis://localhost:6379/0)")
    redis_enabled: bool = Field(default=False, description="Enable Redis caching for distributed deployments")
    redis_key_prefix: str = Field(default="gitcanvas:", description="Redis key prefix used to isolate this app's keys")

    # CORS configuration
    allowed_origins: str = Field(
        default="*",
        description="Comma-separated list of allowed CORS origins, or '*' to allow all (not recommended for production)",
    )

    def allowed_origins_list(self) -> list[str]:
        """Return parsed list of allowed origins."""
        if self.allowed_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    # Cache-clear endpoint protection
    cache_clear_enabled: bool = Field(
        default=False,
        description="Enable cache-clear endpoints; should remain disabled in production unless explicitly needed",
    )
    cache_clear_allow_localhost_only: bool = Field(
        default=True,
        description="Allow cache-clear endpoints only from localhost when no admin token is configured",
    )
    cache_clear_admin_token: Optional[SecretStr] = Field(
        default=None,
        description="Optional admin token required to call cache-clear endpoints",
    )

    @field_validator("github_token", "openai_api_key", "gemini_api_key", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("redis_key_prefix", mode="before")
    @classmethod
    def normalize_redis_key_prefix(cls, v):
        if v is None:
            return "gitcanvas:"
        prefix = str(v).strip() or "gitcanvas:"
        if not prefix.endswith(":"):
            prefix += ":"
        return prefix

    def github_token_value(self) -> Optional[str]:
        return _secret_plain(self.github_token)

    def openai_api_key_value(self) -> Optional[str]:
        return _secret_plain(self.openai_api_key)

    def gemini_api_key_value(self) -> Optional[str]:
        return _secret_plain(self.gemini_api_key)

    def cache_clear_admin_token_value(self) -> Optional[str]:
        return _secret_plain(self.cache_clear_admin_token)

    @property
    def has_github_token(self) -> bool:
        if self.github_token_value() is not None:
            return True
        try:
            from utils.github_tokens import configured_tokens

            return bool(configured_tokens())
        except (ImportError, RuntimeError, TypeError):
            return False

    @property
    def has_any_llm_key(self) -> bool:
        return bool(self.openai_api_key_value() or self.gemini_api_key_value())

    def log_backend_warnings(self) -> None:
        """Log non-fatal configuration issues when starting the API."""
        if not self.has_github_token:
            logger.warning("No server-side GitHub token is configured: GitHub requests use anonymous rate limits.")
        if not self.has_any_llm_key:
            logger.warning(
                "Neither OPENAI_API_KEY nor GEMINI_API_KEY is set: "
                "the Streamlit AI roast feature has no cloud LLM keys in this environment."
            )


@lru_cache
def get_settings() -> GitCanvasSettings:
    return GitCanvasSettings()
