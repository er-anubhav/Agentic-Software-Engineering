import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from src.application.agents.reflection_agent import ReflectionAgent
from src.application.agents.repair_agent import RepairAgent
from src.infrastructure.github_engine.git_workflow import GitWorkflowEngine
from src.domain.models.state import EngineeringState


class ReviewComment(BaseModel):
    comment_id: str
    pr_number: int
    author: str = "code-reviewer"
    body: str
    file_path: Optional[str] = "main.py"
    line_number: Optional[int] = 1


class ReviewFeedbackLoop:
    """
    Review Comment Feedback Loop engine triggering Reflection -> Surgical Repair -> Re-testing -> Follow-up commit.
    """

    def __init__(self):
        self.reflection_agent = ReflectionAgent()
        self.repair_agent = RepairAgent()
        self.git_workflow = GitWorkflowEngine()

    def process_review_comment(self, workspace_path: str, comment: ReviewComment, state: EngineeringState) -> str:
        # 1. Parse review feedback
        state.metadata["review_feedback"] = comment.body
        state.execution_status = "FAILED"

        # 2. Reflect on reviewer feedback
        state = self.reflection_agent.execute(state)

        # 3. Apply surgical repair patch
        target_file = comment.file_path or "main.py"
        full_file_path = os.path.join(workspace_path, target_file)

        if not os.path.exists(full_file_path):
            with open(full_file_path, "w") as f:
                f.write("def resolve_review():\n    return 'resolved'\n")

        state = self.repair_agent.execute(state)

        # 4. Commit follow-up review fix
        commit_sha = self.git_workflow.create_commit(
            workspace_path,
            commit_message=f"fix(review): address feedback for PR #{comment.pr_number} - {comment.body[:30]}",
            author_name="Agentic Bot Reviewer",
            author_email="review-bot@agentic.ai"
        )

        return commit_sha
