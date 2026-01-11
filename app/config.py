"""Application configuration using pydantic-settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "RechnungsChecker"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/rechnungschecker"
    )

    # Redis
    redis_url: RedisDsn = Field(default="redis://localhost:6379/0")

    # Security
    secret_key: str = Field(default="CHANGE-ME-IN-PRODUCTION-USE-SECURE-KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # KoSIT Validator
    kosit_jar_path: Path = Field(default=Path("kosit/validationtool-1.5.0-standalone.jar"))
    kosit_scenarios_path: Path = Field(default=Path("kosit/scenarios.xml"))
    kosit_timeout_seconds: int = 30

    # File Upload
    max_upload_size_mb: int = 25
    temp_file_ttl_seconds: int = 3600  # 1 hour

    # Rate Limiting
    guest_validations_limit: int = 5
    guest_rate_limit_per_minute: int = 10
    auth_rate_limit_per_minute: int = 100

    # Stripe
    stripe_secret_key: str = Field(default="")
    stripe_webhook_secret: str = Field(default="")
    stripe_price_starter: str = Field(default="")
    stripe_price_pro: str = Field(default="")
    stripe_price_steuerberater: str = Field(default="")

    # Email (Mailgun)
    mailgun_api_key: str = Field(default="")
    mailgun_domain: str = Field(default="")
    email_from: str = Field(default="noreply@rechnungschecker.de")

    # Sentry
    sentry_dsn: str = Field(default="")

    @property
    def max_upload_size_bytes(self) -> int:
        """Return max upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
