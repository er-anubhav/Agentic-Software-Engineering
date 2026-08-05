from typing import Dict, Any, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class GovernancePolicy(BaseModel):
    policy_id: str = "policy_default"
    max_autonomy_level: str = "HIGH"  # LOW, MEDIUM, HIGH, FULL
    require_human_approval_for_deploy: bool = True
    prohibited_actions: List[str] = Field(default_factory=lambda: ["host_eval", "rm_rf_root", "force_push_main"])
    emergency_kill_switch_active: bool = False


class SwarmGovernanceEngine:
    """
    Governance & Policy Engine.
    Controls autonomy levels, approval thresholds, security boundaries, compliance rules,
    and emergency shutdown across the swarm.
    """

    def __init__(self, policy: Optional[GovernancePolicy] = None):
        self.policy = policy or GovernancePolicy()

    def validate_action(self, agent_id: str, action: str) -> bool:
        if self.policy.emergency_kill_switch_active:
            return False  # Emergency shutdown active

        action_lower = action.lower()
        for prohibited in self.policy.prohibited_actions:
            if prohibited.lower() in action_lower:
                return False

        return True

    def trigger_emergency_shutdown(self) -> None:
        self.policy.emergency_kill_switch_active = True
