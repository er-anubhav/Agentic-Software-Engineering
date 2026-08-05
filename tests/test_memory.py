import unittest
from src.infrastructure.storage.memory.graph_db import CodeGraph, GraphNode, GraphRelationship, HAS_NEO4J
from src.infrastructure.storage.memory.vector_store import VectorMemoryStore, compute_cosine_similarity
from src.infrastructure.storage.memory.hybrid_memory import HybridMemoryEngine


class TestMemory(unittest.TestCase):

    def test_neo4j_cypher_execution_and_summary(self):
        self.assertTrue(HAS_NEO4J, "neo4j package must be installed")
        graph = CodeGraph()
        summary = graph.get_summary()
        self.assertIn("total_nodes", summary)
        self.assertIn("total_relationships", summary)
        self.assertIn("neo4j_driver_available", summary)

    def test_cosine_similarity_math(self):
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        v3 = [0.0, 1.0, 0.0]

        self.assertAlmostEqual(compute_cosine_similarity(v1, v2), 1.0)
        self.assertAlmostEqual(compute_cosine_similarity(v1, v3), 0.0)

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

    def test_vector_store_fastembed_qdrant_cosine(self):
        vstore = VectorMemoryStore()
        doc1 = vstore.add_document("d1", "FastAPI web REST framework authentication endpoint")
        doc2 = vstore.add_document("d2", "PostgreSQL relational database schema migration table")

        self.assertIsNotNone(doc1.vector)
        self.assertEqual(len(doc1.vector), 384)

        res = vstore.search("FastAPI authentication", top_k=1)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].id, "d1")
        self.assertGreater(res[0].score, 0.0)

    def test_hybrid_memory_engine_fusion(self):
        graph = CodeGraph()
        fn1 = GraphNode(id="file1.py::login", label="Function", name="login")
        fn2 = GraphNode(id="file2.py::auth_check", label="Function", name="auth_check")
        graph.add_node(fn1)
        graph.add_node(fn2)
        graph.add_relationship(GraphRelationship(source_id="file2.py::auth_check", target_id="file1.py::login", rel_type="CALLS"))

        vstore = VectorMemoryStore()
        vstore.add_document("doc1", "Authentication JWT token validator service")

        engine = HybridMemoryEngine(graph=graph, vector_store=vstore)
        res = engine.query("login Authentication JWT")

        self.assertIn("graph_summary", res)
        self.assertIn("intent", res)
        self.assertIn("ranked_snippets", res)
        self.assertIn("context_prompt_text", res)
        self.assertGreater(len(res["ranked_snippets"]), 0)


if __name__ == "__main__":
    unittest.main()
