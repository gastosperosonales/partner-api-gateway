"""
Application Configuration
Uses pydantic-settings for environment variable management
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Gateway Settings
    app_name: str = "API Gateway"
    app_version: str = "1.0.0"

    # Server Settings
    host: str = "0.0.0.0"
    port: int = 5000

    # Database Settings
    database_url: str = "sqlite:///./api_gateway.db"

    # Backend Service URL
    backend_base_url: str = "https://jsonplaceholder.typicode.com"

    # Rate Limiting Defaults
    default_rate_limit: int = 60  # requests per window
    rate_limit_window: int = 60  # seconds

    # Available Services
    available_services: List[str] = [
        "users", "posts", "comments", "todos", "albums", "photos"
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()
