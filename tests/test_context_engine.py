import unittest
from memory.graph_db import CodeGraph, GraphNode, GraphRelationship
from memory.vector_store import VectorMemoryStore
from memory.context_engine import ContextEngine


class TestContextEngine(unittest.TestCase):

    def test_intent_detection(self):
        engine = ContextEngine()
        self.assertEqual(engine.detect_intent("Fix division by zero bug in main.py"), "bugfix")
        self.assertEqual(engine.detect_intent("Refactor helper functions"), "refactor")
        self.assertEqual(engine.detect_intent("Create new database migration"), "feature")

    def test_entity_extraction(self):
        engine = ContextEngine()
        entities = engine.extract_entities("Import parse_config from utils.py")
        self.assertIn("parse_config", entities)
        self.assertIn("utils.py", entities)

    def test_reciprocal_rank_fusion_pipeline(self):
        graph = CodeGraph()
        fn1 = GraphNode(id="auth.py::verify_token", label="Function", name="verify_token", repo_id="repo1")
        fn2 = GraphNode(id="api.py::login_route", label="Function", name="login_route", repo_id="repo1")
        graph.add_node(fn1)
        graph.add_node(fn2)
        graph.add_relationship(GraphRelationship(source_id="api.py::login_route", target_id="auth.py::verify_token", rel_type="CALLS", repo_id="repo1"))

        vstore = VectorMemoryStore()
        vstore.add_document("doc1", "JWT token verification service", repo_id="repo1")
        vstore.add_document("doc2", "PostgreSQL database client", repo_id="repo2")

        engine = ContextEngine(graph=graph, vector_store=vstore)
        payload = engine.query("verify_token JWT auth", repo_id="repo1", top_k=5)

        self.assertEqual(payload.repo_id, "repo1")
        self.assertEqual(payload.intent, "qa")
        self.assertGreater(len(payload.ranked_snippets), 0)
        self.assertIsNotNone(payload.assembled_prompt_context)

        # Confirm multi-tenant isolation (repo2 doc not in snippets for repo1)
        snippet_ids = [s.id for s in payload.ranked_snippets]
        self.assertNotIn("doc2", snippet_ids)


if __name__ == "__main__":
    unittest.main()
