import unittest
from src.application.orchestration.dag_compiler import DAGCompiler, TaskDAG, DAGNode


class TestDAGCompiler(unittest.TestCase):

    def test_dag_node_creation_and_ready(self):
        dag = TaskDAG()
        n1 = DAGNode(id="n1", step=1, agent="A1", objective="Obj 1")
        n2 = DAGNode(id="n2", step=2, agent="A2", objective="Obj 2", dependencies=["n1"])
        dag.add_node(n1)
        dag.add_node(n2)

        ready = dag.get_ready_nodes()
        self.assertEqual(len(ready), 1)
        self.assertEqual(ready[0].id, "n1")

        n1.status = "COMPLETED"
        ready_after = dag.get_ready_nodes()
        self.assertEqual(len(ready_after), 1)
        self.assertEqual(ready_after[0].id, "n2")

    def test_cycle_detection(self):
        dag = TaskDAG()
        n1 = DAGNode(id="n1", step=1, agent="A1", objective="Obj 1", dependencies=["n2"])
        n2 = DAGNode(id="n2", step=2, agent="A2", objective="Obj 2", dependencies=["n1"])
        dag.add_node(n1)
        dag.add_node(n2)

        self.assertTrue(dag.has_cycles())

    def test_dynamic_dag_compiler(self):
        compiler = DAGCompiler()
        tasks = [
            "Design Database Schema",
            "Design REST API Routes",
            "Implement Code Logic",
            "Run Pytest Test Suite"
        ]
        dag = compiler.compile(tasks)
        self.assertFalse(dag.has_cycles())
        sorted_nodes = dag.get_topological_sort()
        self.assertEqual(len(sorted_nodes), 4)
        self.assertEqual(sorted_nodes[0].owner_agent, "DatabaseAgent")


if __name__ == "__main__":
    unittest.main()
