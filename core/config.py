import os
from pydantic import BaseModel, Field


class Settings(BaseModel):
    app_name: str = "Agentic Software Engineering Platform"
    version: str = "2.0.0-alpha"
    debug: bool = False
    ollama_model: str = Field(default="qwen2.5-coder:7b")
    ollama_temperature: float = Field(default=0.0)
    repository_path: str = Field(default_factory=lambda: os.getcwd())
    output_dir: str = Field(default="generated_project")


def get_settings() -> Settings:
    return Settings()
