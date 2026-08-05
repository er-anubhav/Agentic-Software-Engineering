"""
src.core.config — Layer 0: System Configuration & Modular Domain Config Hierarchy.
"""
import os
from typing import Optional
from pydantic import BaseModel, Field


class BaseConfig(BaseModel):
    app_name: str = "Agentic Software Engineering Platform"
    version: str = "2.0.0"


class EnvironmentConfig(BaseModel):
    environment: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = Field(default_factory=lambda: os.getenv("DEBUG", "true").lower() == "true")
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))


class SecretsConfig(BaseModel):
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    anthropic_api_key: str = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    jwt_secret_key: str = Field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", "insecure_dev_secret"))

    def sanitize(self) -> dict:
        return {
            "has_openai_key": bool(self.openai_api_key),
            "has_anthropic_key": bool(self.anthropic_api_key),
            "has_gemini_key": bool(self.gemini_api_key),
        }


class RuntimeConfig(BaseModel):
    sqlite_db_path: str = Field(default_factory=lambda: os.getenv("SQLITE_DB_PATH", "platform.db"))
    ollama_base_url: str = Field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    max_concurrent_workers: int = Field(default_factory=lambda: int(os.getenv("MAX_WORKERS", "10")))


class Settings(BaseModel):
    app_name: str = "Agentic Software Engineering Platform"
    version: str = "2.0.0-alpha"
    repository_path: str = Field(default_factory=os.getcwd)
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    sqlite_db_path: str = Field(default_factory=lambda: os.getenv("SQLITE_DB_PATH", "platform.db"))
    openai_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    anthropic_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    gemini_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    ollama_base_url: str = Field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    jwt_secret_key: str = Field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", "insecure_dev_secret"))
    base: BaseConfig = Field(default_factory=BaseConfig)
    env: EnvironmentConfig = Field(default_factory=EnvironmentConfig)
    secrets: SecretsConfig = Field(default_factory=SecretsConfig)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)


def get_settings() -> Settings:
    return Settings()
