import os
import shutil
import subprocess
import time

from sandboxes.base_sandbox import BaseSandbox, SandboxConfig, SandboxResult


class LocalSandbox(BaseSandbox):
    """
    Isolated directory-based local execution sandbox.
    """

    def __init__(self, base_dir: str = "/tmp/sandbox_workspace", config: SandboxConfig = None):
        super().__init__(config)
        self.workspace_dir = os.path.abspath(base_dir)

    def start(self) -> None:
        os.makedirs(self.workspace_dir, exist_ok=True)

    def write_file(self, relative_path: str, content: str) -> None:
        full_path = os.path.join(self.workspace_dir, relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

    def read_file(self, relative_path: str) -> str:
        full_path = os.path.join(self.workspace_dir, relative_path)
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()

    def execute_command(self, command: str) -> SandboxResult:
        start_time = time.time()
        try:
            res = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace_dir,
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
                stderr=f"Command timed out after {self.config.timeout_seconds} seconds",
                traceback=f"TimeoutExpired: {command}",
                duration_ms=duration
            )

    def stop(self) -> None:
        if os.path.exists(self.workspace_dir):
            try:
                shutil.rmtree(self.workspace_dir)
            except Exception:
                pass
