from typing import Dict, Any, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel


class GateDecision(BaseModel):
    approved: bool
    operation: str
    reason: str


class HumanApprovalGate:
    """
    Human Approval Gate intercepting high-risk operations (deployment, destructive migrations, force push).
    """

    HIGH_RISK_KEYWORDS = {
        "deploy", "k8s_apply", "force_push", "db_drop", "secret_access", "merge_main"
    }

    def check_operation(self, operation_name: str, auto_approve_safe: bool = True) -> GateDecision:
        op_lower = operation_name.lower()
        is_high_risk = any(kw in op_lower for kw in self.HIGH_RISK_KEYWORDS)

        if is_high_risk:
            return GateDecision(
                approved=False,
                operation=operation_name,
                reason=f"Operation '{operation_name}' is high risk and requires explicit human gate approval."
            )

        return GateDecision(
            approved=True,
            operation=operation_name,
            reason=f"Operation '{operation_name}' passed automated safety check."
        )

    def approve_operation(self, operation_name: str) -> GateDecision:
        return GateDecision(
            approved=True,
            operation=operation_name,
            reason=f"Human reviewer manually approved operation '{operation_name}'."
        )
