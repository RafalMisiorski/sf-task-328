from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./app.db"

    # Security
    secret_key: str = "dev-secret-key-change-in-production"

    # Environment
    environment: str = "development"
    debug: bool = True

    # API
    api_title: str = "API"
    api_version: str = "1.0.0"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()