import os
import ast
import subprocess
from typing import Dict, Any, List, Optional

from agents.base_agent import BaseAgent
from models.state import EngineeringState
from memory.graph_db import CodeGraph, GraphNode, GraphRelationship
from memory.vector_store import VectorMemoryStore
from codebase_intelligence.polyglot_parser import PolyglotParser, ASTSymbol
from codebase_intelligence.scip_index import SCIPDatabase, SCIPSymbol
from codebase_intelligence.semantic_chunker import SemanticChunker, CodeChunk
from codebase_intelligence.symbol_search import SymbolSearchEngine
from codebase_intelligence.health_metrics import RepositoryHealthMetricsEngine, HealthMetricsReport


class CodebaseAnalysisAgent(BaseAgent):
    """
    Production-Grade Polyglot Semantic Indexing & SCIP Code Intelligence Engine (RFC-006).
    Performs Sourcegraph SCIP-style symbol indexing, AST-aware semantic chunking,
    polyglot multi-language parsing (Python, TS/JS, Java, Go, C/C++, Rust),
    incremental git-diff updates, symbol search API queries, and repository health metrics.
    """

    def __init__(self):
        super().__init__()
        self.polyglot_parser = PolyglotParser()
        self.semantic_chunker = SemanticChunker()

    def execute(self, state: EngineeringState):
        if not state.repository_path or not os.path.exists(state.repository_path):
            state.codebase_analysis = {
                "project_type": "greenfield",
                "message": "No valid repository path supplied."
            }
            return state

        repo_id = getattr(state, "repo_id", None) or os.path.basename(os.path.abspath(state.repository_path))
        graph = CodeGraph()
        vector_store = VectorMemoryStore()
        scip_db = SCIPDatabase(repository_id=repo_id)

        analysis = {
            "project_type": "brownfield",
            "repo_id": repo_id,
            "project_structure": [],
            "python_files": [],
            "polyglot_files": [],
            "classes": [],
            "functions": [],
            "imports": [],
            "apis": [],
            "database_models": [],
            "dependencies": [],
            "dependency_graph": {},
            "code_graph": graph,
            "vector_store": vector_store,
            "scip_db": scip_db,
            "symbol_search": SymbolSearchEngine(scip_db),
            "health_metrics": None
        }

        SKIP_DIRS = {
            ".git", ".idea", ".vscode", "__pycache__", ".pytest_cache",
            ".venv", "venv", "env", "site-packages", "build", "dist", "generated_project"
        }

        batch_nodes: List[GraphNode] = []
        batch_rels: List[GraphRelationship] = []
        batch_docs: List[Dict[str, Any]] = []

        for root, dirs, files in os.walk(state.repository_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for file in files:
                path = os.path.join(root, file)
                rel_path = os.path.relpath(path, state.repository_path)
                analysis["project_structure"].append(path)

                ext = os.path.splitext(file)[1].lower()
                if ext in self.polyglot_parser.SUPPORTED_EXTENSIONS:
                    analysis["polyglot_files"].append(path)
                    if ext == ".py":
                        analysis["python_files"].append(path)

                    file_node = GraphNode(id=rel_path, label="File", name=file, repo_id=repo_id)
                    batch_nodes.append(file_node)

                    # Read content & perform AST semantic chunking
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        if content.strip():
                            chunks = self.semantic_chunker.chunk_file(repo_id, rel_path, content)
                            for chunk in chunks:
                                batch_docs.append({
                                    "id": f"{repo_id}::{chunk.chunk_id}",
                                    "text": chunk.content,
                                    "metadata": {
                                        "file_path": rel_path,
                                        "filename": file,
                                        "chunk_type": chunk.chunk_type,
                                        "ast_path": chunk.ast_path
                                    }
                                })

                            # Polyglot AST Parsing & SCIP Symbol Registration
                            symbols = self.polyglot_parser.parse_file(rel_path, content)
                            for sym in symbols:
                                scip_sym = SCIPSymbol(
                                    symbol_id=f"{rel_path}::{sym.name}",
                                    repository=repo_id,
                                    file_path=rel_path,
                                    range_lines=[sym.start_line, sym.end_line],
                                    kind=sym.kind,
                                    language=sym.language,
                                    definition_snippet=f"{sym.kind} {sym.name}"
                                )
                                scip_db.register_symbol(scip_sym)

                                sym_node = GraphNode(
                                    id=scip_sym.symbol_id,
                                    label=sym.kind.capitalize(),
                                    name=sym.name,
                                    repo_id=repo_id
                                )
                                batch_nodes.append(sym_node)
                                batch_rels.append(GraphRelationship(
                                    source_id=file_node.id,
                                    target_id=sym_node.id,
                                    rel_type="CONTAINS",
                                    repo_id=repo_id
                                ))

                                if sym.kind == "class":
                                    analysis["classes"].append({"name": sym.name, "file": rel_path})
                                elif sym.kind == "function":
                                    analysis["functions"].append({"name": sym.name, "file": rel_path})

                    except Exception:
                        pass

                elif file.lower() == "requirements.txt":
                    self.read_requirements(path, analysis)

        # Batch ingestion via ONNX FastEmbed vectors and Cypher UNWIND
        if batch_nodes:
            graph.add_nodes_batch(repo_id, batch_nodes)
        if batch_rels:
            graph.add_relationships_batch(repo_id, batch_rels)
        if batch_docs:
            vector_store.add_documents_batch(repo_id, batch_docs)

        # Calculate Repository Health Metrics
        analysis["health_metrics"] = RepositoryHealthMetricsEngine.calculate_metrics(repo_id, scip_db, len(analysis["polyglot_files"]))

        print("\n===== Polyglot Semantic Code Intelligence Engine (RFC-006) =====")
        print(f"Repo ID           : {repo_id}")
        print(f"Project Type      : {analysis['project_type']}")
        print(f"Polyglot Files    : {len(analysis['polyglot_files'])}")
        print(f"SCIP Symbols      : {len(scip_db.symbols)}")
        print(f"Graph Nodes       : {len(graph.nodes)}")
        print(f"Health Score      : {analysis['health_metrics'].overall_health_score}/100.0")

        state.codebase_analysis = analysis
        return state

    def read_requirements(self, filename, analysis):
        for encoding in ["utf-8", "utf-16", "latin-1"]:
            try:
                with open(filename, "r", encoding=encoding) as f:
                    for line in f:
                        dependency = line.strip()
                        if dependency and not dependency.startswith("#"):
                            analysis["dependencies"].append(dependency)
                return
            except Exception:
                continue