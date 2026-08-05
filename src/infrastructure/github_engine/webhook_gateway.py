import uuid
import time
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from src.domain.models.state import EngineeringState
from src.infrastructure.observability.tracer import Tracer


class WebhookEvent(BaseModel):
    event_type: str  # issues, issue_comment, pull_request, push, installation
    action: str = "opened"
    repository: str
    issue_number: Optional[int] = None
    pr_number: Optional[int] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    trace_id: str = Field(default_factory=lambda: f"trace_{uuid.uuid4().hex[:12]}")
    correlation_id: str = Field(default_factory=lambda: f"corr_{uuid.uuid4().hex[:8]}")


class WebhookGateway:
    """
    Webhook Gateway mapping incoming GitHub events to executable EngineeringState workflows.
    """

    def process_webhook(self, event_type: str, payload: Dict[str, Any]) -> EngineeringState:
        tracer = Tracer.get_instance()
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        trace = tracer.start_trace(run_id=run_id)

        repository = payload.get("repository", {}).get("full_name", "owner/repo")
        action = payload.get("action", "opened")

        event = WebhookEvent(
            event_type=event_type,
            action=action,
            repository=repository,
            payload=payload,
            trace_id=trace.trace_id
        )

        state = EngineeringState()
        state.repo_id = repository.replace("/", "_")
        state.metadata["trace_id"] = trace.trace_id
        state.metadata["correlation_id"] = event.correlation_id
        state.metadata["github_event_type"] = event_type
        state.metadata["github_repository"] = repository

        if event_type == "issues":
            issue_data = payload.get("issue", {})
            event.issue_number = issue_data.get("number", 1)
            state.user_prompt = f"Resolve Issue #{event.issue_number}: {issue_data.get('title', '')}\n\n{issue_data.get('body', '')}"
            state.metadata["issue_number"] = event.issue_number

        elif event_type == "issue_comment":
            comment_data = payload.get("comment", {})
            event.issue_number = payload.get("issue", {}).get("number", 1)
            state.user_prompt = f"PR Review Feedback on Issue #{event.issue_number}: {comment_data.get('body', '')}"
            state.metadata["issue_number"] = event.issue_number
            state.metadata["is_review_feedback"] = True

        return state
