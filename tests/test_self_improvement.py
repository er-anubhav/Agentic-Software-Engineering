import unittest

from learning.experience_store import ExperienceStore, EngineeringExperience
from learning.planner_optimizer import PlannerOptimizer
from learning.retrieval_optimizer import RetrievalOptimizer
from learning.model_optimizer import ModelOptimizer
from learning.prompt_evolution import PromptEvolutionEngine, PromptVariant
from learning.pattern_mining import PatternMiningEngine
from learning.knowledge_distillation import KnowledgeDistillationEngine
from learning.self_improvement_engine import SelfImprovementEngine


class TestSelfImprovementEngine(unittest.TestCase):

    def setUp(self):
        self.store = ExperienceStore.get_instance()
        self.planner_opt = PlannerOptimizer(self.store)
        self.retrieval_opt = RetrievalOptimizer()
        self.model_opt = ModelOptimizer()
        self.prompt_evo = PromptEvolutionEngine()
        self.pattern_miner = PatternMiningEngine(self.store)
        self.distiller = KnowledgeDistillationEngine()
        self.engine = SelfImprovementEngine.get_instance()

    def test_experience_persistence(self):
        exp = EngineeringExperience(
            experience_id="exp_101",
            workflow_id="wf_101",
            task_category="feature_development",
            trajectory=["plan", "code", "verify"],
            success=True,
            cost_usd=0.04,
            duration_sec=15.0
        )
        self.store.record_experience(exp)

        experiences = self.store.get_experiences_by_category("feature_development")
        self.assertGreaterEqual(len(experiences), 1)
        self.assertEqual(experiences[0].workflow_id, "wf_101")

    def test_pattern_mining_accuracy(self):
        patterns = self.pattern_miner.mine_patterns()
        self.assertGreaterEqual(len(patterns), 2)
        pattern_types = [p.pattern_type for p in patterns]
        self.assertIn("bug_pattern", pattern_types)
        self.assertIn("repair_strategy", pattern_types)

    def test_planner_optimization_recommendation(self):
        rec = self.planner_opt.optimize_planning("feature_development")
        self.assertGreater(rec.recommended_dag_depth, 0)
        self.assertGreater(rec.confidence, 0.8)

    def test_retrieval_optimization(self):
        weights = self.retrieval_opt.tune_weights({"retrieval_precision": 96.0})
        self.assertGreater(weights.scip_symbol_weight, 0.3)

    def test_prompt_evolution_tournament(self):
        v1 = PromptVariant(variant_id="p_v1", prompt_name="repair_prompt", version="v1", pass_rate=88.0)
        v2 = PromptVariant(variant_id="p_v2", prompt_name="repair_prompt", version="v2", pass_rate=96.5)

        self.prompt_evo.register_variant(v1)
        self.prompt_evo.register_variant(v2)

        tournament = self.prompt_evo.run_tournament("repair_prompt")
        self.assertEqual(tournament.winning_version, "v2")
        self.assertIn("p_v1", tournament.retired_variant_ids)

    def test_model_routing_optimization(self):
        ranking_repair = self.model_opt.rank_models_for_task("surgical_repair")
        self.assertEqual(ranking_repair.primary_provider, "anthropic")

        ranking_retrieval = self.model_opt.rank_models_for_task("semantic_retrieval")
        self.assertEqual(ranking_retrieval.primary_provider, "gemini")

    def test_knowledge_distillation(self):
        patterns = self.pattern_miner.mine_patterns()
        playbook = self.distiller.distill_playbook("feature_development", patterns)
        self.assertEqual(playbook.target_category, "feature_development")
        self.assertGreater(len(playbook.steps), 0)

    def test_end_to_end_self_improvement_execution(self):
        cycle_result = self.engine.run_self_improvement_cycle("feature_development")
        self.assertTrue(cycle_result.improvement_verified)
        self.assertFalse(cycle_result.regression_detected)
        self.assertIsNotNone(cycle_result.distilled_playbook)


if __name__ == "__main__":
    unittest.main()
