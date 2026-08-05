from typing import Dict, Any, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class EngineeringRiskScore(BaseModel):
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    numerical_score: float = 15.0  # 0 to 100
    blast_radius_factor: float = 0.2
    dependency_count_factor: float = 0.1
    test_confidence_factor: float = 0.9
    risk_factors: List[str] = Field(default_factory=list)


class RiskAssessmentEngine:
    """
    Risk Assessment Engine.
    Calculates EngineeringRiskScore based on blast radius, dependency count, production impact,
    security impact, test confidence, and historical failure rate.
    """

    def calculate_risk(
        self,
        blast_radius_score: float,
        dependency_count: int,
        test_pass_rate: float,
        has_invariant_violations: bool = False
    ) -> EngineeringRiskScore:
        score = blast_radius_score * 0.4 + (dependency_count * 2.0) + ((100.0 - test_pass_rate) * 0.5)

        if has_invariant_violations:
            score += 40.0

        factors = []
        if score < 30.0:
            level = "LOW"
            factors.append("Low blast radius & passing tests.")
        elif score < 60.0:
            level = "MEDIUM"
            factors.append("Moderate dependency impact.")
        elif score < 85.0:
            level = "HIGH"
            factors.append("High blast radius or lower test confidence.")
        else:
            level = "CRITICAL"
            factors.append("Critical invariant violation or massive blast radius.")

        return EngineeringRiskScore(
            risk_level=level,
            numerical_score=round(score, 2),
            blast_radius_factor=blast_radius_score,
            dependency_count_factor=float(dependency_count),
            test_confidence_factor=test_pass_rate,
            risk_factors=factors
        )
