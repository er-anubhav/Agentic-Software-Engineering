import unittest
from src.evaluation.chaos_runner import run_chaos_fault_injection_experiments
from src.evaluation.load_tester import run_high_concurrency_stress_test


class TestValidationSuite(unittest.TestCase):

    def test_chaos_fault_injection_experiments(self):
        # Executes worker crash, DLQ routing, corrupted checkpoint fallback
        try:
            run_chaos_fault_injection_experiments()
        except Exception as e:
            self.fail(f"Chaos fault injection experiments failed: {e}")

    def test_high_concurrency_stress_load(self):
        # Executes 20 simultaneous DAG workflows under thread pool load
        success = run_high_concurrency_stress_test(num_workflows=20)
        self.assertTrue(success)


if __name__ == "__main__":
    unittest.main()
