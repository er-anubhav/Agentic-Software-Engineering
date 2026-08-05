"""
src.domain.value_objects.confidence_score — Immutable Value Object for Reasoning & Verification.
"""
from typing import List
from pydantic import BaseModel, Field


class ConfidenceScore(BaseModel):
    """
    Domain Value Object representing AI decision confidence.
    Dynamically derives risk level to prevent inconsistent internal state.
    """
    score: float = Field(default=0.95, ge=0.0, le=1.0)
    missing_context: List[str] = Field(default_factory=list)
    recommended_action: str = "EXECUTE"

    @property
    def risk_level(self) -> str:
        """Dynamically derives risk level from score to eliminate inconsistent state."""
        if self.score >= 0.85:
            return "LOW"
        elif self.score >= 0.70:
            return "MEDIUM"
        elif self.score >= 0.50:
            return "HIGH"
        return "CRITICAL"

    def is_high_confidence(self) -> bool:
        """Returns True if score meets high confidence threshold (>= 0.85)."""
        return self.score >= 0.85

    def requires_human_review(self) -> bool:
        """Returns True if confidence falls below threshold (< 0.70) or risk is HIGH/CRITICAL."""
        return self.score < 0.70 or self.risk_level in ("HIGH", "CRITICAL")

    def combine(self, other: "ConfidenceScore") -> "ConfidenceScore":
        """Combines two confidence scores taking the minimum score and merging contexts."""
        combined_score = round(min(self.score, other.score), 4)
        missing = list(set(self.missing_context + other.missing_context))
        return ConfidenceScore(
            score=combined_score,
            missing_context=missing,
            recommended_action="REVIEW" if (self.requires_human_review() or other.requires_human_review()) else "EXECUTE"
        )
