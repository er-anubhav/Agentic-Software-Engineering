import os
import shutil
import hmac
import hashlib
import uuid
import unittest
from github_engine.app_auth import GitHubAppAuth
from github_engine.webhook_gateway import WebhookGateway
from github_engine.workspace_manager import RepositoryWorkspaceManager
from github_engine.git_workflow import GitWorkflowEngine
from github_engine.pr_engine import AutonomousPREngine
from github_engine.review_loop import ReviewFeedbackLoop, ReviewComment
from github_engine.github_mcp_tools import register_github_mcp_tools
from github_engine.orchestrator import GitHubAutonomousOrchestrator
from mcp_runtime.tool_registry import MCPToolRegistry
from models.state import EngineeringState


class TestGitHubAutonomousWorkflow(unittest.TestCase):

    def setUp(self):
        self.auth = GitHubAppAuth(webhook_secret="test_secret_123")
        self.gateway = WebhookGateway()
        self.workspace_mgr = RepositoryWorkspaceManager()
        self.git_workflow = GitWorkflowEngine()
        self.pr_engine = AutonomousPREngine()
        self.review_loop = ReviewFeedbackLoop()

        self.test_repo_dir = f"/tmp/test_github_local_repo_{uuid.uuid4().hex[:8]}"
        os.makedirs(self.test_repo_dir, exist_ok=True)
        with open(os.path.join(self.test_repo_dir, "main.py"), "w") as f:
            f.write("def hello():\n    return 'hello'\n")

        import subprocess
        subprocess.run(["git", "init"], cwd=self.test_repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=self.test_repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=self.test_repo_dir, check=True, capture_output=True)

    def tearDown(self):
        if os.path.exists(self.test_repo_dir):
            shutil.rmtree(self.test_repo_dir, ignore_errors=True)

    def test_github_app_auth_signature_validation(self):
        payload = b'{"action": "opened", "issue": {"number": 1}}'
        signature = "sha256=" + hmac.new(b"test_secret_123", payload, hashlib.sha256).hexdigest()

        is_valid = self.auth.verify_signature(payload, signature)
        self.assertTrue(is_valid)

        is_invalid = self.auth.verify_signature(payload, "sha256=invalid_signature")
        self.assertFalse(is_invalid)

    def test_webhook_gateway_issue_conversion(self):
        payload = {
            "action": "opened",
            "repository": {"full_name": "org/agentic-se"},
            "issue": {"number": 42, "title": "Fix API Bug", "body": "API returns 500 error"}
        }

        state = self.gateway.process_webhook("issues", payload)
        self.assertEqual(state.metadata["github_repository"], "org/agentic-se")
        self.assertEqual(state.metadata["issue_number"], 42)
        self.assertIn("trace_id", state.metadata)
        self.assertIn("correlation_id", state.metadata)

    def test_workspace_manager_and_git_workflow(self):
        session = self.workspace_mgr.create_workspace("org/agentic-se", existing_local_repo=self.test_repo_dir)
        try:
            self.assertTrue(os.path.exists(session.workspace_path))

            branch = self.git_workflow.create_feature_branch(session.workspace_path, "feat/issue-42")
            self.assertEqual(branch, "feat/issue-42")

            with open(os.path.join(session.workspace_path, "main.py"), "a") as f:
                f.write("\ndef feature():\n    return 42\n")

            commit_sha = self.git_workflow.create_commit(session.workspace_path, "feat: add feature")
            self.assertEqual(len(commit_sha), 40)
        finally:
            self.workspace_mgr.cleanup_workspace(session)

    def test_autonomous_pr_engine_formatting(self):
        pr = self.pr_engine.generate_pull_request(
            repository="org/agentic-se",
            issue_number=42,
            issue_title="Fix API Bug",
            head_branch="feat/issue-42",
            commit_sha="a1b2c3d4e5f67890",
            summary="Fixed API endpoint error."
        )

        self.assertEqual(pr.pr_number, 42)
        self.assertIn("Issue #42", pr.title)
        self.assertIn("Evaluation Benchmark Score", pr.body)
        self.assertIn("Rollback & Safety Strategy", pr.body)

    def test_review_feedback_loop(self):
        session = self.workspace_mgr.create_workspace("org/agentic-se", existing_local_repo=self.test_repo_dir)
        try:
            state = EngineeringState()
            state.repository_path = session.workspace_path

            comment = ReviewComment(
                comment_id="c_1",
                pr_number=42,
                body="Please fix syntax bug in main.py",
                file_path="main.py"
            )

            commit_sha = self.review_loop.process_review_comment(session.workspace_path, comment, state)
            self.assertEqual(len(commit_sha), 40)
        finally:
            self.workspace_mgr.cleanup_workspace(session)

    def test_github_mcp_tools_registration(self):
        register_github_mcp_tools()
        registry = MCPToolRegistry.get_instance()
        repo_tool = registry.get_tool("github_repository")
        pr_tool = registry.get_tool("github_pr")

        self.assertIsNotNone(repo_tool)
        self.assertIsNotNone(pr_tool)

    def test_end_to_end_github_autonomous_orchestrator(self):
        orchestrator = GitHubAutonomousOrchestrator()
        payload = {
            "action": "opened",
            "repository": {"full_name": "org/agentic-se"},
            "issue": {"number": 101, "title": "Build user auth route", "body": "Need JWT auth route"}
        }

        pr_data = orchestrator.handle_github_event("issues", payload, existing_local_repo=self.test_repo_dir)

        self.assertEqual(pr_data.pr_number, 101)
        self.assertIn("Issue #101", pr_data.title)
        self.assertEqual(len(pr_data.commit_sha), 40)


if __name__ == "__main__":
    unittest.main()
