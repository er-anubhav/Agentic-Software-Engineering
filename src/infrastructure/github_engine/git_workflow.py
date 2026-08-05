import os
import subprocess
from typing import List, Optional
class GitWorkflowEngine:
    """
    Git Workflow Engine handling branch creation, commits, rebasing, and merge conflict detection.
    """
    def create_feature_branch(self, workspace_path: str, branch_name: str) -> str:
        subprocess.run(["git", "checkout", "-b", branch_name], cwd=workspace_path, check=True, capture_output=True)
        return branch_name
    def create_commit(self, workspace_path: str, commit_message: str, author_name: str = "Agentic Bot", author_email: str = "bot@agentic.ai") -> str:
        subprocess.run(["git", "add", "."], cwd=workspace_path, check=True, capture_output=True)
        env = os.environ.copy()
        env["GIT_AUTHOR_NAME"] = author_name
        env["GIT_AUTHOR_EMAIL"] = author_email
        env["GIT_COMMITTER_NAME"] = author_name
        env["GIT_COMMITTER_EMAIL"] = author_email
        subprocess.run(["git", "commit", "--allow-empty", "-m", commit_message], cwd=workspace_path, env=env, check=True, capture_output=True)
        res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=workspace_path, check=True, capture_output=True, text=True)
        return res.stdout.strip()
    def check_merge_conflicts(self, workspace_path: str, target_branch: str = "main") -> bool:
        try:
            res = subprocess.run(["git", "merge-tree", target_branch, "HEAD"], cwd=workspace_path, capture_output=True, text=True)
            return "+<<" in res.stdout or "conflict" in res.stdout.lower()
        except Exception as e:
            return False
