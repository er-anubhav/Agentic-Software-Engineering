import uuid
import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class SubtaskNegotiation(BaseModel):
    request_id: str = Field(default_factory=lambda: f"neg_{uuid.uuid4().hex[:8]}")
    requesting_agent: str
    target_agent: str
    subtask_description: str
    accepted: bool = False
    response_reason: str = "Accepted subtask delegation"
    timestamp: float = Field(default_factory=time.time)


class AgentNegotiator:
    """
    Facilitates dynamic subtask negotiation and capability transfers between specialized agents.
    """

    def request_subtask_delegation(self, requesting_agent: str, target_agent: str, subtask_description: str) -> SubtaskNegotiation:
        # Agent accepts negotiation if target agent is registered
        accepted = True if target_agent in (
            "DatabaseAgent", "APIAgent", "CodeGenerationAgent",
            "TestGenerationAgent", "ValidationAgent", "SecurityAgent", "DevOpsAgent"
        ) else False

        reason = f"{target_agent} accepted subtask delegation for '{subtask_description[:30]}...'" if accepted else f"{target_agent} unavailable"

        return SubtaskNegotiation(
            requesting_agent=requesting_agent,
            target_agent=target_agent,
            subtask_description=subtask_description,
            accepted=accepted,
            response_reason=reason
        )
