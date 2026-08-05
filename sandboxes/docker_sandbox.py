import os
import time
import logging
import subprocess
from typing import Optional

from sandboxes.base_sandbox import BaseSandbox, SandboxConfig, SandboxResult, SandboxUnavailableException
from sandboxes.local_sandbox import LocalSandbox

logger = logging.getLogger(__name__)


class DockerSandbox(BaseSandbox):
    """
    Production-grade Containerized Docker sandbox provider with strict security isolation.
    Refuses host fallback execution in production to prevent unisolated code execution.
    """

    def __init__(self, workspace_path: str = "generated_project", config: Optional[SandboxConfig] = None, allow_local_fallback: bool = False):
        super().__init__(config)
        self.workspace_path = os.path.abspath(workspace_path)
        self.allow_local_fallback = allow_local_fallback
        self.fallback = LocalSandbox(base_dir=self.workspace_path, config=self.config) if self.allow_local_fallback else None
        self.docker_available = self._check_docker()

    def _check_docker(self) -> bool:
        try:
            res = subprocess.run(["docker", "info"], capture_output=True, timeout=3)
            return res.returncode == 0
        except Exception:
            return False

    def start(self) -> None:
        os.makedirs(self.workspace_path, exist_ok=True)
        if not self.docker_available:
            if self.allow_local_fallback and self.fallback:
                logger.warning("CRITICAL SECURITY NOTICE: Docker unavailable. Using LocalSandbox fallback (allow_local_fallback=True).")
                self.fallback.start()
            else:
                logger.error("Docker daemon unavailable. Refusing host LocalSandbox fallback execution.")
                raise SandboxUnavailableException("Docker sandbox runtime is unavailable. Refusing host execution for security compliance.")

    def write_file(self, relative_path: str, content: str) -> None:
        full_path = os.path.join(self.workspace_path, relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

    def read_file(self, relative_path: str) -> str:
        full_path = os.path.join(self.workspace_path, relative_path)
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()

    def execute_command(self, command: str) -> SandboxResult:
        if not self.docker_available:
            if self.allow_local_fallback and self.fallback:
                return self.fallback.execute_command(command)
            else:
                raise SandboxUnavailableException("Docker sandbox runtime is unavailable. Aborting command execution.")

        start_time = time.time()
        docker_cmd = [
            "docker", "run", "--rm",
            "-v", f"{self.workspace_path}:/workspace",
            "-w", "/workspace",
            self.config.environment_id,
            "sh", "-c", command
        ]
        try:
            res = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds
            )
            duration = (time.time() - start_time) * 1000
            return SandboxResult(
                exit_code=res.returncode,
                stdout=res.stdout,
                stderr=res.stderr,
                traceback=res.stderr if res.returncode != 0 else None,
                duration_ms=duration
            )
        except subprocess.TimeoutExpired as e:
            duration = (time.time() - start_time) * 1000
            return SandboxResult(
                exit_code=124,
                stdout=e.stdout or "",
                stderr=f"Docker sandbox command timed out after {self.config.timeout_seconds}s",
                traceback=f"TimeoutExpired: {command}",
                duration_ms=duration
            )

    def stop(self) -> None:
        if not self.docker_available and self.allow_local_fallback and self.fallback:
            self.fallback.stop()
