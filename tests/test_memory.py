import unittest
from memory.graph_db import CodeGraph, GraphNode, GraphRelationship
from memory.vector_store import VectorMemoryStore
from memory.hybrid_memory import HybridMemoryEngine


class TestMemory(unittest.TestCase):

    def test_code_graph_operations(self):
        graph = CodeGraph()
        f1 = GraphNode(id="file1.py", label="File", name="file1.py")
        fn1 = GraphNode(id="file1.py::foo", label="Function", name="foo")
        fn2 = GraphNode(id="file2.py::bar", label="Function", name="bar")

        graph.add_node(f1)
        graph.add_node(fn1)
        graph.add_node(fn2)

        graph.add_relationship(GraphRelationship(source_id="file2.py::bar", target_id="file1.py::foo", rel_type="CALLS"))

        callers = graph.find_callers("foo")
        self.assertEqual(len(callers), 1)
        self.assertEqual(callers[0].name, "bar")

    def test_vector_store_search(self):
        vstore = VectorMemoryStore()
        vstore.add_document("d1", "FastAPI web REST framework")
        vstore.add_document("d2", "PostgreSQL relational database schema")

        res = vstore.search("FastAPI framework", top_k=1)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].id, "d1")

    def test_hybrid_memory_engine(self):
        graph = CodeGraph()
        vstore = VectorMemoryStore()
        vstore.add_document("doc1", "Authentication JWT token service")

        engine = HybridMemoryEngine(graph=graph, vector_store=vstore)
        res = engine.query("Authentication JWT")
        self.assertIn("graph_summary", res)
        self.assertEqual(len(res["relevant_snippets"]), 1)


if __name__ == "__main__":
    unittest.main()
