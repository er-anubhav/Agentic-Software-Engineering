from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SandboxConfig(BaseModel):
    environment_id: str = "python:3.12-slim"
    timeout_seconds: int = 30
    workdir: str = "/workspace"
    env_vars: Dict[str, str] = Field(default_factory=dict)


class SandboxResult(BaseModel):
    exit_code: int
    stdout: str
    stderr: str
    traceback: Optional[str] = None
    duration_ms: float = 0.0


class BaseSandbox(ABC):
    """
    Abstract isolation sandbox interface for code execution, building, and testing.
    """

    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def write_file(self, relative_path: str, content: str) -> None:
        pass

    @abstractmethod
    def read_file(self, relative_path: str) -> str:
        pass

    @abstractmethod
    def execute_command(self, command: str) -> SandboxResult:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass
