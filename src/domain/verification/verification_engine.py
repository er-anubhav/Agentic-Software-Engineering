from typing import Dict, Any, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

from src.domain.verification.contracts import EngineeringContract, PreCondition, PostCondition, Invariant, SafetyRule
from src.domain.verification.symbolic_executor import SymbolicExecutor, SymbolicExecutionResult
from src.domain.verification.semantic_validator import SemanticValidator, SemanticEquivalenceResult
from src.domain.verification.impact_analysis import DependencyImpactAnalyzer, ImpactReport
from src.domain.verification.invariant_engine import InvariantEngine, InvariantViolation
from src.domain.verification.risk_engine import RiskAssessmentEngine, EngineeringRiskScore
from src.domain.verification.deployment_gate import DeploymentGate, DeploymentGateResult
from src.domain.verification.rollback_engine import AutomaticRollbackEngine, RollbackPlan


class VerificationReport(BaseModel):
    report_id: str
    target_file: str
    contracts_valid: bool = True
    semantic_result: SemanticEquivalenceResult
    impact_report: ImpactReport
    invariant_violations: List[InvariantViolation] = Field(default_factory=list)
    symbolic_result: SymbolicExecutionResult
    risk_score: EngineeringRiskScore
    deployment_gate_result: DeploymentGateResult
    recommended_rollback_plan: Optional[RollbackPlan] = None
    verification_passed: bool = True


class UnifiedVerificationEngine:
    """
    Central Formal Verification, Execution Safety & Semantic Validation Engine (RFC-015).
    Coordinates:
      Contracts -> Semantic Validation -> Impact Analysis -> Invariant Checking ->
      Symbolic Validation -> Risk Analysis -> Deployment Gate -> Rollback Recommendation
    """

    _instance: Optional["UnifiedVerificationEngine"] = None

    def __init__(self):
        self.symbolic_executor = SymbolicExecutor()
        self.semantic_validator = SemanticValidator()
        self.impact_analyzer = DependencyImpactAnalyzer()
        self.invariant_engine = InvariantEngine()
        self.risk_engine = RiskAssessmentEngine()
        self.deployment_gate = DeploymentGate()
        self.rollback_engine = AutomaticRollbackEngine()

    @classmethod
    def get_instance(cls) -> "UnifiedVerificationEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def verify_patch(
        self,
        file_path: str,
        original_code: str,
        patched_code: str,
        test_pass_rate: float = 100.0
    ) -> VerificationReport:
        # Step 1: Contracts Check
        contract = EngineeringContract(
            contract_id=f"contract_{file_path}",
            target_symbol=file_path,
            pre_conditions=[PreCondition(name="non_empty_code", condition_expression="len(patched_code) > 0")],
            post_conditions=[PostCondition(name="valid_syntax", condition_expression="syntax_check == True")]
        )
        contracts_valid = contract.validate_all()

        # Step 2: Semantic Equivalence Validation
        semantic_res = self.semantic_validator.validate_patch_semantics(original_code, patched_code)

        # Step 3: Dependency Impact Analysis
        impact_rep = self.impact_analyzer.analyze_impact(file_path)

        # Step 4: Invariant Verification
        invariant_violations = self.invariant_engine.verify_invariants(file_path, patched_code)

        # Step 5: Symbolic Execution
        symbolic_res = self.symbolic_executor.analyze_symbolic_paths(file_path, patched_code)

        # Step 6: Risk Assessment
        risk_score = self.risk_engine.calculate_risk(
            blast_radius_score=impact_rep.blast_radius_score,
            dependency_count=impact_rep.downstream_dependency_count,
            test_pass_rate=test_pass_rate,
            has_invariant_violations=len(invariant_violations) > 0
        )

        # Step 7: Deployment Safety Gate
        gate_res = self.deployment_gate.evaluate_gate(
            risk_level=risk_score.risk_level,
            invariant_violations_count=len(invariant_violations),
            is_equivalent=semantic_res.is_equivalent,
            test_pass_rate=test_pass_rate
        )

        # Step 8: Rollback Plan
        rollback_plan = None
        if not gate_res.gate_passed or len(invariant_violations) > 0:
            rollback_plan = self.rollback_engine.plan_rollback("verification_step")

        overall_passed = gate_res.gate_passed and len(invariant_violations) == 0

        return VerificationReport(
            report_id=f"verif_rep_{file_path}",
            target_file=file_path,
            contracts_valid=contracts_valid,
            semantic_result=semantic_res,
            impact_report=impact_rep,
            invariant_violations=invariant_violations,
            symbolic_result=symbolic_res,
            risk_score=risk_score,
            deployment_gate_result=gate_res,
            recommended_rollback_plan=rollback_plan,
            verification_passed=overall_passed
        )
