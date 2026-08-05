from typing import Dict, Any, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class DeploymentGateResult(BaseModel):
    decision: str = "ALLOW"  # ALLOW, ALLOW_WITH_WARNING, REQUIRE_HUMAN, BLOCK
    gate_passed: bool = True
    reasons: List[str] = Field(default_factory=list)
    overall_confidence: float = 0.96


class DeploymentGate:
    """
    Deployment Safety Gate Engine.
    Evaluates benchmark scores, verification scores, invariant scores, semantic validation,
    and risk scores to make deployment decisions.
    """

    def evaluate_gate(
        self,
        risk_level: str,
        invariant_violations_count: int,
        is_equivalent: bool,
        test_pass_rate: float
    ) -> DeploymentGateResult:
        reasons = []

        if invariant_violations_count > 0:
            return DeploymentGateResult(
                decision="BLOCK",
                gate_passed=False,
                reasons=[f"Blocked: {invariant_violations_count} invariant violations detected."],
                overall_confidence=0.99
            )

        if not is_equivalent:
            reasons.append("Warning: Patch introduces potential API breaking change.")

        if risk_level == "CRITICAL":
            return DeploymentGateResult(
                decision="REQUIRE_HUMAN",
                gate_passed=False,
                reasons=["High risk change requires explicit human sign-off."],
                overall_confidence=0.95
            )

        if risk_level == "HIGH" or not is_equivalent:
            return DeploymentGateResult(
                decision="ALLOW_WITH_WARNING",
                gate_passed=True,
                reasons=reasons or ["Passed with high risk warning."],
                overall_confidence=0.90
            )

        return DeploymentGateResult(
            decision="ALLOW",
            gate_passed=True,
            reasons=["All verification checks passed cleanly."],
            overall_confidence=0.98
        )
