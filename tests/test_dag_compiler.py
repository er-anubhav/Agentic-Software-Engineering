import unittest
from orchestrator.dag_compiler import DAGCompiler, TaskDAG, DAGNode


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

    def test_dag_compiler(self):
        compiler = DAGCompiler()
        dag = compiler.compile(["Task 1"])
        self.assertFalse(dag.has_cycles())
        sorted_nodes = dag.get_topological_sort()
        self.assertEqual(len(sorted_nodes), 8)


if __name__ == "__main__":
    unittest.main()
