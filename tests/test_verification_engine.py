import unittest

from verification.contracts import EngineeringContract, PreCondition, PostCondition
from verification.symbolic_executor import SymbolicExecutor
from verification.semantic_validator import SemanticValidator
from verification.impact_analysis import DependencyImpactAnalyzer
from verification.invariant_engine import InvariantEngine
from verification.risk_engine import RiskAssessmentEngine
from verification.deployment_gate import DeploymentGate
from verification.rollback_engine import AutomaticRollbackEngine
from verification.verification_engine import UnifiedVerificationEngine


class TestFormalVerificationEngine(unittest.TestCase):

    def setUp(self):
        self.symbolic_executor = SymbolicExecutor()
        self.semantic_validator = SemanticValidator()
        self.impact_analyzer = DependencyImpactAnalyzer()
        self.invariant_engine = InvariantEngine()
        self.risk_engine = RiskAssessmentEngine()
        self.deployment_gate = DeploymentGate()
        self.rollback_engine = AutomaticRollbackEngine()
        self.engine = UnifiedVerificationEngine.get_instance()

    def test_contract_validation(self):
        contract = EngineeringContract(
            contract_id="c1",
            target_symbol="foo",
            pre_conditions=[PreCondition(name="pre1", condition_expression="x > 0", passed=True)],
            post_conditions=[PostCondition(name="post1", condition_expression="result != None", passed=True)]
        )
        self.assertTrue(contract.validate_all())

        contract_bad = EngineeringContract(
            contract_id="c2",
            target_symbol="bar",
            pre_conditions=[PreCondition(name="pre1", condition_expression="x > 0", passed=False)]
        )
        self.assertFalse(contract_bad.validate_all())

    def test_symbolic_execution(self):
        res = self.symbolic_executor.analyze_symbolic_paths("main.py", "if False:\n    print('dead')")
        self.assertGreater(res.explored_branches, 0)
        self.assertEqual(len(res.dead_code_lines), 1)

    def test_semantic_equivalence_validation(self):
        orig = "def process(): return 42"
        patched = "def process():\n    # Add logging\n    return 42"
        res = self.semantic_validator.validate_patch_semantics(orig, patched)
        self.assertTrue(res.is_equivalent)

        # Breaking change test
        patched_rename = "def process_renamed(): return 42"
        res_breaking = self.semantic_validator.validate_patch_semantics(orig, patched_rename)
        self.assertFalse(res_breaking.is_equivalent)

    def test_dependency_impact_analysis(self):
        impact = self.impact_analyzer.analyze_impact("auth.py")
        self.assertGreater(impact.downstream_dependency_count, 0)
        self.assertGreater(impact.blast_radius_score, 0)

    def test_invariant_failures_detection(self):
        violations = self.invariant_engine.verify_invariants("db.py", "select * from users")
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].invariant_name, "tenant_isolation")

    def test_risk_scoring(self):
        risk_low = self.risk_engine.calculate_risk(blast_radius_score=10.0, dependency_count=1, test_pass_rate=100.0)
        self.assertEqual(risk_low.risk_level, "LOW")

        risk_crit = self.risk_engine.calculate_risk(blast_radius_score=80.0, dependency_count=10, test_pass_rate=50.0, has_invariant_violations=True)
        self.assertEqual(risk_crit.risk_level, "CRITICAL")

    def test_deployment_gate_decisions(self):
        gate_allow = self.deployment_gate.evaluate_gate("LOW", 0, True, 100.0)
        self.assertEqual(gate_allow.decision, "ALLOW")

        gate_block = self.deployment_gate.evaluate_gate("LOW", 1, True, 100.0)
        self.assertEqual(gate_block.decision, "BLOCK")

    def test_rollback_planning(self):
        plan = self.rollback_engine.plan_rollback("step_api", "chk_100")
        self.assertTrue(plan.is_safe_to_rollback)
        self.assertEqual(plan.target_checkpoint_id, "chk_100")

    def test_end_to_end_verification_pipeline(self):
        orig = "def add(a, b): return a + b"
        patched = "def add(a, b):\n    return a + b"

        report = self.engine.verify_patch("math_util.py", orig, patched)
        self.assertTrue(report.verification_passed)
        self.assertEqual(report.deployment_gate_result.decision, "ALLOW")


if __name__ == "__main__":
    unittest.main()
