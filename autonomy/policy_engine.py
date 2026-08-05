from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from autonomy.progress_engine import ProgressReport


class PolicyAction(str, Enum):
    CONTINUE = "CONTINUE"
    RETRY = "RETRY"
    ROLLBACK = "ROLLBACK"
    ASK_HUMAN = "ASK_HUMAN"
    ESCALATE = "ESCALATE"
    ABORT = "ABORT"


class PolicyDecision(BaseModel):
    action: PolicyAction
    reason: str
    target_node_id: Optional[str] = None


class ExecutionPolicyEngine:
    """
    Determines execution actions (CONTINUE, RETRY, ROLLBACK, ASK_HUMAN, ESCALATE, ABORT) based on policy rules.
    """

    def evaluate_policy(self, progress: ProgressReport, failure_count: int = 0, is_high_risk: bool = False) -> PolicyDecision:
        if is_high_risk:
            return PolicyDecision(action=PolicyAction.ASK_HUMAN, reason="High-risk operation requires human approval.")

        if failure_count >= 5:
            return PolicyDecision(action=PolicyAction.ABORT, reason="Exceeded maximum allowable failure retries (5).")

        if failure_count >= 3:
            return PolicyDecision(action=PolicyAction.ROLLBACK, reason="3 consecutive failures encountered. Rolling back state.")

        if progress.is_stagnant:
            return PolicyDecision(action=PolicyAction.RETRY, reason="Execution stagnant. Triggering retry with elevated priority.")

        return PolicyDecision(action=PolicyAction.CONTINUE, reason="Progress normal. Continuing execution.")
