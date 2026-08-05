import os
import shutil
import tempfile
import subprocess
from typing import Optional
from pydantic import BaseModel


class WorkspaceSession(BaseModel):
    workspace_id: str
    repository: str
    workspace_path: str
    target_branch: str = "main"


class RepositoryWorkspaceManager:
    """
    Isolated Repository Workspace Manager handling workspace creation, caching, and cleanup.
    """

    def __init__(self, base_dir: str = "/tmp/agentic_github_workspaces"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def create_workspace(self, repository: str, existing_local_repo: Optional[str] = None) -> WorkspaceSession:
        safe_name = repository.replace("/", "_")
        workspace_path = tempfile.mkdtemp(prefix=f"ws_{safe_name}_", dir=self.base_dir)

        if existing_local_repo and os.path.exists(existing_local_repo):
            # Clone from local directory for fast testing
            subprocess.run(["git", "clone", existing_local_repo, workspace_path], check=True, capture_output=True)
        else:
            # Initialize git repository
            subprocess.run(["git", "init", workspace_path], check=True, capture_output=True)
            with open(os.path.join(workspace_path, "README.md"), "w") as f:
                f.write(f"# {repository}\nInitial repo setup.\n")
            subprocess.run(["git", "add", "."], cwd=workspace_path, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=workspace_path, check=True, capture_output=True)

        return WorkspaceSession(
            workspace_id=os.path.basename(workspace_path),
            repository=repository,
            workspace_path=workspace_path
        )

    def cleanup_workspace(self, session: WorkspaceSession) -> None:
        if os.path.exists(session.workspace_path):
            shutil.rmtree(session.workspace_path, ignore_errors=True)
