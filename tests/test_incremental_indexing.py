import os
import shutil
import tempfile
import unittest
from src.domain.models.state import EngineeringState
from src.application.agents.codebase_analysis_agent import CodebaseAnalysisAgent


class TestIncrementalIndexing(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        with open(os.path.join(self.test_dir, "main.py"), "w") as f:
            f.write("def foo():\n    return 42\n")
        with open(os.path.join(self.test_dir, "utils.py"), "w") as f:
            f.write("def helper():\n    pass\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_full_batch_analysis(self):
        agent = CodebaseAnalysisAgent()
        state = EngineeringState(repository_path=self.test_dir)
        state = agent.execute(state)

        analysis = state.codebase_analysis
        self.assertEqual(len(analysis["python_files"]), 2)
        self.assertEqual(len(analysis["functions"]), 2)

        graph = analysis["code_graph"]
        self.assertGreater(len(graph.nodes), 0)


if __name__ == "__main__":
    unittest.main()
