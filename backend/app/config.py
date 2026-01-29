"""
InsightX AI - Configuration Module

Loads environment variables and provides type-safe configuration.
Fails fast if required variables are not set.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Required: Gemini API Configuration
    gemini_api_key: str
    gemini_model: str = "gemini-1.5-flash"
    
    # CORS Configuration
    frontend_origin: str = "http://localhost:3000"
    
    # Data Configuration
    data_path: str = "./data/transactions.csv"
    
    # Session Configuration
    max_context_turns: int = 6
    
    # Rate Limiting
    rate_limit_per_min: int = 10
    
    # Optional: Redis for session storage
    redis_url: Optional[str] = None
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Uses lru_cache to ensure settings are loaded only once.
    Raises ValidationError if GEMINI_API_KEY is not set.
    """
    return Settings()


def validate_settings() -> None:
    """
    Validate that all required settings are properly configured.
    Call this at application startup to fail fast.
    """
    settings = get_settings()
    
    if not settings.gemini_api_key or settings.gemini_api_key == "your_gemini_api_key_here":
        raise ValueError(
            "GEMINI_API_KEY is not set or is using the placeholder value. "
            "Please set a valid Gemini API key in your .env file."
        )
    
    # Log configuration (without sensitive data)
    print(f"✓ Configuration loaded:")
    print(f"  - Gemini Model: {settings.gemini_model}")
    print(f"  - Frontend Origin: {settings.frontend_origin}")
    print(f"  - Data Path: {settings.data_path}")
    print(f"  - Max Context Turns: {settings.max_context_turns}")
    print(f"  - Rate Limit: {settings.rate_limit_per_min}/min")
    print(f"  - Redis: {'Enabled' if settings.redis_url else 'Disabled (in-memory)'}")
