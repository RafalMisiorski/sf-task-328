"""
Application Configuration

This module uses Pydantic Settings for configuration management.
Environment variables are loaded from .env file automatically.

WHY: Centralized configuration makes it easy to change settings without code changes.
WHY: Pydantic validation ensures configuration is correct at startup.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Create a .env file in the project root with these values:
    - SECRET_KEY: Used for JWT token signing (MUST be changed in production)
    - DATABASE_URL: Database connection string
    - ALLOWED_ORIGINS: Comma-separated list of CORS origins
    """

    # Application
    app_name: str = "My FastAPI App"
    debug: bool = False

    # Environment (useful for conditional behavior)
    environment: str = "development"  # development, staging, production

    # Database
    # v37.1 FIX: Accept both database_url and DATABASE_URL (fixes Task #544)
    # Agent sometimes generates settings.DATABASE_URL, so we support both
    database_url: str = "sqlite:///./app.db"

    # Alias for compatibility
    @property
    def DATABASE_URL(self) -> str:
        """Alias for database_url (uppercase compatibility)."""
        return self.database_url

    # Security - JWT
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Ignore extra environment variables
    )

    @property
    def origins_list(self) -> List[str]:
        """Convert comma-separated origins to list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]


# Global settings instance
# WHY: Single instance pattern - settings are loaded once at startup
settings = Settings()
