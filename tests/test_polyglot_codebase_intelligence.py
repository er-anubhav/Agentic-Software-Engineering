import os
import shutil
import unittest
from src.infrastructure.storage.memory.polyglot_parser import PolyglotParser, ASTSymbol
from src.infrastructure.storage.memory.scip_index import SCIPDatabase, SCIPSymbol
from src.infrastructure.storage.memory.semantic_chunker import SemanticChunker
from src.infrastructure.storage.memory.symbol_search import SymbolSearchEngine
from src.infrastructure.storage.memory.health_metrics import RepositoryHealthMetricsEngine
from src.application.agents.codebase_analysis_agent import CodebaseAnalysisAgent
from src.domain.models.state import EngineeringState


class TestPolyglotCodebaseIntelligence(unittest.TestCase):

    def setUp(self):
        self.test_dir = "/tmp/test_polyglot_intelligence_repo"
        os.makedirs(self.test_dir, exist_ok=True)

        # Create multi-language sample files
        with open(os.path.join(self.test_dir, "main.py"), "w") as f:
            f.write("def verify_jwt(token):\n    pass\n\nclass User:\n    pass\n")

        with open(os.path.join(self.test_dir, "app.ts"), "w") as f:
            f.write("interface AuthConfig {\n    secret: string;\n}\n\nfunction authenticateUser() {\n    return true;\n}\n")

        with open(os.path.join(self.test_dir, "server.go"), "w") as f:
            f.write("package main\n\nfunc HandleRequests() {\n}\n")

        with open(os.path.join(self.test_dir, "lib.rs"), "w") as f:
            f.write("pub fn process_data() {\n}\n")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_polyglot_parser_languages(self):
        parser = PolyglotParser()

        py_symbols = parser.parse_file("main.py", "def verify_jwt(token):\n    pass\nclass User:\n    pass")
        self.assertEqual(len(py_symbols), 2)

        ts_symbols = parser.parse_file("app.ts", "interface AuthConfig {}\nfunction authenticateUser() {}")
        self.assertEqual(len(ts_symbols), 2)

        go_symbols = parser.parse_file("server.go", "func HandleRequests() {}")
        self.assertEqual(len(go_symbols), 1)

        rs_symbols = parser.parse_file("lib.rs", "fn process_data() {}")
        self.assertEqual(len(rs_symbols), 1)

    def test_scip_database_symbol_indexing_and_search(self):
        scip_db = SCIPDatabase(repository_id="repo_test")
        sym1 = SCIPSymbol(symbol_id="main.py::verify_jwt", file_path="main.py", definition_snippet="def verify_jwt")
        sym2 = SCIPSymbol(symbol_id="main.py::auth_middleware", file_path="main.py", definition_snippet="def auth_middleware")

        scip_db.register_symbol(sym1)
        scip_db.register_symbol(sym2)
        scip_db.add_call_edge("main.py::auth_middleware", "main.py::verify_jwt")

        self.assertEqual(scip_db.find_callers("main.py::verify_jwt"), ["main.py::auth_middleware"])

        search_engine = SymbolSearchEngine(scip_db)
        callers = search_engine.find_callers("verify_jwt")
        self.assertEqual(len(callers), 1)

        middleware = search_engine.find_middleware()
        self.assertGreaterEqual(len(middleware), 1)

    def test_semantic_chunker_ast_boundaries(self):
        chunker = SemanticChunker()
        content = "SELECT * FROM users WHERE active = 1;\n\nclass UserController:\n    def get_user():\n        pass"
        chunks = chunker.chunk_file("repo_test", "controllers.py", content)

        self.assertGreater(len(chunks), 0)
        types = [c.chunk_type for c in chunks]
        self.assertIn("sql", types)

    def test_repository_health_metrics_engine(self):
        scip_db = SCIPDatabase(repository_id="repo_test")
        sym1 = SCIPSymbol(symbol_id="main.py::unused_func", file_path="main.py", kind="function")
        scip_db.register_symbol(sym1)

        metrics = RepositoryHealthMetricsEngine.calculate_metrics("repo_test", scip_db, files_count=1)
        self.assertIsNotNone(metrics.overall_health_score)
        self.assertEqual(metrics.unused_symbols_count, 1)

    def test_codebase_analysis_agent_polyglot_execution(self):
        agent = CodebaseAnalysisAgent()
        state = EngineeringState()
        state.repository_path = self.test_dir

        state = agent.execute(state)
        analysis = state.codebase_analysis

        self.assertEqual(analysis["project_type"], "brownfield")
        self.assertGreater(len(analysis["polyglot_files"]), 0)
        self.assertIsNotNone(analysis["scip_db"])
        self.assertIsNotNone(analysis["health_metrics"])


if __name__ == "__main__":
    unittest.main()
