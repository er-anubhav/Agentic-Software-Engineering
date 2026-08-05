"""
src/core/config.py — Layer 0: Enterprise Platform Configuration System.
"""
import os
import logging
from functools import lru_cache
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Settings(BaseModel):
    """
    Production Settings Model with Environment Variable Overrides.
    """
    app_name: str = Field(default_factory=lambda: os.getenv("APP_NAME", "Agentic Software Engineering Platform"))
    version: str = Field(default="2.0.0-alpha")
    debug: bool = Field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    environment: str = Field(default_factory=lambda: os.getenv("ENV", "development"))

    # Model / Inference Settings
    ollama_model: str = Field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b"))
    ollama_temperature: float = Field(default_factory=lambda: float(os.getenv("OLLAMA_TEMPERATURE", "0.0")))
    ollama_base_url: str = Field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))

    # Storage & Repository Paths
    repository_path: str = Field(default_factory=lambda: os.getenv("REPOSITORY_PATH", os.getcwd()))
    output_dir: str = Field(default_factory=lambda: os.getenv("OUTPUT_DIR", "generated_project"))

    # Security Settings
    jwt_secret_key: str = Field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", "dev-insecure-secret-change-in-prod"))
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Thread-safe, cached singleton settings instance."""
    return Settings()
