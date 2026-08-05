import os
import shutil
import unittest
from src.domain.models.state import EngineeringState
from src.evaluation.benchmark_dataset import BenchmarkTask, BenchmarkDataset
from src.evaluation.metrics_engine import ExecutionMetrics, PatchComparer, QualityScoreCalculator
from src.evaluation.failure_classifier import FailureClassifier, FailureCategory
from src.evaluation.replay_engine import ReplayEngine, WorkflowTrajectory
from src.evaluation.experiment_tracker import ExperimentTracker, ExperimentRun
from src.evaluation.evaluation_runner import EvaluationRunner


class TestEvaluationHarness(unittest.TestCase):
    def setUp(self):
        self.test_dir = "/tmp/test_eval_harness_output"
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_benchmark_task_and_dataset_serialization(self):
        task1 = BenchmarkTask(
            id="task_001",
            repository="repo_alpha",
            difficulty="EASY",
            language="python",
            issue_description="Fix ZeroDivisionError in math utility module",
            ground_truth_patch="--- a/math_util.py\n+++ b/math_util.py\n@@ -1,2 +1,2 @@\n-x / 0\n+x / 1",
            expected_files=["math_util.py"],
            tags=["bugfix", "math"]
        )

        dataset = BenchmarkDataset(dataset_name="test_suite_v1", tasks=[task1])
        filepath = os.path.join(self.test_dir, "dataset.json")
        dataset.save_to_file(filepath)

        loaded_dataset = BenchmarkDataset.load_from_file(filepath)
        self.assertEqual(loaded_dataset.dataset_name, "test_suite_v1")
        self.assertEqual(len(loaded_dataset.tasks), 1)
        self.assertEqual(loaded_dataset.tasks[0].id, "task_001")

    def test_patch_comparer_diff_and_ast_similarity(self):
        gen_patch = "--- a/main.py\n+++ b/main.py\n@@ -1,2 +1,2 @@\n-def foo(): return 1/0\n+def foo(): return 42"
        ref_patch = "--- a/main.py\n+++ b/main.py\n@@ -1,2 +1,2 @@\n-def foo(): return 1/0\n+def foo(): return 42"

        result = PatchComparer.compare_patches(gen_patch, ref_patch)
        self.assertTrue(result.exact_match)
        self.assertEqual(result.diff_accuracy, 1.0)
        self.assertEqual(result.ast_similarity, 1.0)

    def test_quality_score_calculator(self):
        metrics = ExecutionMetrics(
            planning_time_ms=500.0,
            context_precision=0.9,
            context_recall=0.8,
            repair_attempts=0
        )
        patch_res = PatchComparer.compare_patches("a = 1", "a = 1")
        scores = QualityScoreCalculator.calculate_scores(metrics, patch_res, "PASS")

        self.assertIn("overall_engineering_score", scores)
        self.assertEqual(scores["execution_score"], 100.0)
        self.assertGreater(scores["overall_engineering_score"], 80.0)

    def test_failure_classifier_taxonomy(self):
        self.assertEqual(
            FailureClassifier.classify_failure(traceback_str="SandboxUnavailableException: Refusing host execution"),
            FailureCategory.SECURITY_FAILURE
        )
        self.assertEqual(
            FailureClassifier.classify_failure(traceback_str="SyntaxError: invalid syntax"),
            FailureCategory.COMPILATION_FAILURE
        )
        self.assertEqual(
            FailureClassifier.classify_failure(traceback_str="AssertionError: assert 1 == 2"),
            FailureCategory.TEST_FAILURE
        )
        self.assertEqual(
            FailureClassifier.classify_failure(status="PASS"),
            FailureCategory.NONE
        )

    def test_replay_engine_trajectory(self):
        replay_engine = ReplayEngine(storage_dir=os.path.join(self.test_dir, "trajectories"))
        trajectory = WorkflowTrajectory(run_id="run_100", task_id="task_1", repository="repo_1")

        replay_engine.record_step(trajectory, "PlannerAgent", "plan_dag", {"prompt": "Fix bug"}, {"plan": []}, 150.0)
        path = replay_engine.save_trajectory(trajectory)

        self.assertTrue(os.path.exists(path))
        loaded = replay_engine.load_trajectory("run_100")
        self.assertIsNotNone(loaded)
        self.assertEqual(len(loaded.steps), 1)
        self.assertEqual(loaded.steps[0].agent_name, "PlannerAgent")

    def test_experiment_tracker_and_leaderboard(self):
        tracker = ExperimentTracker(base_dir=self.test_dir)
        run = ExperimentRun(
            run_id="run_eval_test",
            git_sha="abcdef12",
            status="PASS",
            failure_category=FailureCategory.NONE,
            quality_scores={"overall_engineering_score": 95.5, "repair_score": 100.0}
        )

        run_dir = tracker.log_run(run)
        self.assertTrue(os.path.exists(os.path.join(run_dir, "metrics.json")))
        self.assertTrue(os.path.exists(os.path.join(run_dir, "evaluation.json")))

        leaderboard_path = os.path.join(self.test_dir, "leaderboard.md")
        self.assertTrue(os.path.exists(leaderboard_path))
        with open(leaderboard_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("run_eval", content)
        self.assertIn("95.5", content)

    def test_evaluation_runner_benchmark_execution(self):
        runner = EvaluationRunner(output_dir=self.test_dir)
        task = BenchmarkTask(
            id="task_demo_01",
            repository="repo_demo",
            difficulty="EASY",
            issue_description="Fix addition logic in calculator app",
            expected_files=["calc.py"]
        )

        mock_state = EngineeringState()
        mock_state.execution_status = "COMPLETED"
        mock_state.metadata = {"repair_attempts": 0, "tokens_used": 1500, "generated_patch": "a = 1"}

        with unittest.mock.patch("src.application.orchestration.workflow.Workflow.execute", return_value=mock_state):
            run = runner.run_benchmark_task(task)
            self.assertIsNotNone(run.run_id)
            self.assertEqual(run.status, "PASS")
            self.assertIn("overall_engineering_score", run.quality_scores)


if __name__ == "__main__":
    unittest.main()
