import unittest
from reasoning.structured_outputs import (
    PlanningDecision,
    RepairDecision,
    ExecutionDecision,
    EvaluationDecision,
    ConfidenceScore
)
from reasoning.token_budget import ModelRouter, TokenBudgetManager, ModelTier
from reasoning.prompt_library import PromptLibrary, PromptTemplate, AutomaticPromptOptimizer
from reasoning.retry_policy import ReasoningRetryPolicy
from reasoning.self_critique import SelfCritiqueEngine
from reasoning.multi_agent_debate import MultiAgentDebateEngine
from reasoning.reflection_memory import ReasoningReflectionMemory, ReasoningTrajectory
from reasoning.reasoning_engine import UnifiedReasoningEngine


class TestAgenticReasoningEngine(unittest.TestCase):

    def setUp(self):
        self.engine = UnifiedReasoningEngine.get_instance()
        self.router = ModelRouter()
        self.budget_mgr = TokenBudgetManager()
        self.prompt_lib = PromptLibrary()
        self.critique_engine = SelfCritiqueEngine()
        self.debate_engine = MultiAgentDebateEngine()
        self.reflection_memory = ReasoningReflectionMemory.get_instance()

    def test_structured_outputs_models(self):
        conf = ConfidenceScore(score=0.98, risk_level="LOW")
        plan = PlanningDecision(
            goal_id="goal_1",
            task_dag_ids=["n1", "n2"],
            selected_tools=["git", "docker"],
            confidence=conf
        )

        self.assertEqual(plan.confidence.score, 0.98)
        self.assertEqual(len(plan.selected_tools), 2)

    def test_model_router_and_token_budget(self):
        tier_cheap = self.router.route_task("summarization")
        self.assertEqual(tier_cheap, ModelTier.CHEAP)

        tier_large = self.router.route_task("surgical repair")
        self.assertEqual(tier_large, ModelTier.LARGE)

        cost = self.budget_mgr.record_usage(prompt_tokens=1000, completion_tokens=500, tier=ModelTier.LARGE)
        self.assertGreater(cost, 0.0)
        self.assertGreater(self.budget_mgr.current_spent_usd, 0.0)

    def test_prompt_library_and_automatic_optimizer(self):
        p1 = PromptTemplate(name="test_prompt", version="v1", template_str="P1", benchmark_score=85.0)
        p2 = PromptTemplate(name="test_prompt", version="v2", template_str="P2", benchmark_score=96.5)

        self.prompt_lib.register_prompt(p1)
        self.prompt_lib.register_prompt(p2)

        best_p = AutomaticPromptOptimizer.select_best_prompt([p1, p2])
        self.assertEqual(best_p.version, "v2")
        self.assertEqual(best_p.benchmark_score, 96.5)

    def test_retry_policy_execution(self):
        policy = ReasoningRetryPolicy(max_retries=2)
        res = policy.execute_with_retry(lambda: 42)
        self.assertEqual(res, 42)

    def test_self_critique_engine(self):
        critique = self.critique_engine.critique_and_improve("def add(a, b): return a + b")
        self.assertIn("Refined via Self-Critique", critique.improved_action)
        self.assertGreater(critique.quality_score, 90.0)

    def test_multi_agent_debate_consensus(self):
        consensus = self.debate_engine.conduct_debate("Migrate database schema")
        self.assertTrue(consensus.consensus_reached)
        self.assertIn("PlannerAgent", consensus.agent_opinions)
        self.assertIn("SecurityAgent", consensus.agent_opinions)

    def test_reflection_memory(self):
        traj = ReasoningTrajectory(
            trajectory_id="t1",
            task_type="repair",
            chosen_tools=["git"],
            confidence_score=0.97,
            success=True
        )
        self.reflection_memory.record_trajectory(traj)

        retrieved = self.reflection_memory.get_similar_trajectories("repair")
        self.assertGreaterEqual(len(retrieved), 1)

    def test_unified_reasoning_engine_decisions(self):
        plan_decision = self.engine.make_planning_decision("Build REST API", ["git", "docker", "postgres"])
        self.assertEqual(plan_decision.confidence.risk_level, "LOW")

        repair_decision = self.engine.make_repair_decision("main.py", "ZeroDivisionError: division by zero")
        self.assertEqual(repair_decision.patch_type, "unified_diff")
        self.assertIn("Refined via Self-Critique", repair_decision.suggested_patch)


if __name__ == "__main__":
    unittest.main()
