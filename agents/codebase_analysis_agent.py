import os
import ast
import subprocess
from typing import Dict, Any, List, Optional

from agents.base_agent import BaseAgent
from models.state import EngineeringState
from memory.graph_db import CodeGraph, GraphNode, GraphRelationship
from memory.vector_store import VectorMemoryStore


class CodebaseAnalysisAgent(BaseAgent):

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

        analysis = {
            "project_type": "brownfield",
            "repo_id": repo_id,
            "project_structure": [],
            "python_files": [],
            "classes": [],
            "functions": [],
            "imports": [],
            "apis": [],
            "database_models": [],
            "dependencies": [],
            "dependency_graph": {},
            "code_graph": graph,
            "vector_store": vector_store
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

                if file.endswith(".py"):
                    analysis["python_files"].append(path)
                    file_node = GraphNode(id=rel_path, label="File", name=file, repo_id=repo_id)
                    batch_nodes.append(file_node)

                    # Prepare vector chunk document
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        if content.strip():
                            batch_docs.append({
                                "id": f"{repo_id}::{rel_path}",
                                "text": content[:2000],  # first 2k chars
                                "metadata": {"file_path": rel_path, "filename": file}
                            })
                    except Exception:
                        pass

                    self.analyze_python(path, rel_path, repo_id, analysis, batch_nodes, batch_rels, file_node)

                elif file.lower() == "requirements.txt":
                    self.read_requirements(path, analysis)

        # Batch ingestion via ONNX vector embedding and Cypher UNWIND
        if batch_nodes:
            graph.add_nodes_batch(repo_id, batch_nodes)
        if batch_rels:
            graph.add_relationships_batch(repo_id, batch_rels)
        if batch_docs:
            vector_store.add_documents_batch(repo_id, batch_docs)

        print("\n===== Codebase Analysis (Full Batch Indexing) =====")
        print(f"Repo ID      : {repo_id}")
        print(f"Project Type : {analysis['project_type']}")
        print(f"Python Files : {len(analysis['python_files'])}")
        print(f"Classes      : {len(analysis['classes'])}")
        print(f"Functions    : {len(analysis['functions'])}")
        print(f"Graph Nodes  : {len(graph.nodes)}")

        state.codebase_analysis = analysis
        return state

    def analyze_incremental(self, state: EngineeringState, base_commit: str = "HEAD~1") -> EngineeringState:
        """
        Epic 3: Incremental git-diff based AST re-parsing, stale node deletion,
        and batch embedding updating.
        """
        if not state.repository_path or not os.path.exists(state.repository_path):
            return state

        repo_id = getattr(state, "repo_id", None) or os.path.basename(os.path.abspath(state.repository_path))
        analysis = state.codebase_analysis or {}
        graph = analysis.get("code_graph") or CodeGraph()
        vector_store = analysis.get("vector_store") or VectorMemoryStore()

        try:
            cmd = ["git", "diff", "--name-status", base_commit]
            result = subprocess.run(cmd, cwd=state.repository_path, capture_output=True, text=True, check=True)
            diff_lines = result.stdout.strip().split("\n")
        except Exception as e:
            self.logger.warning(f"Git diff incremental check failed: {e}. Falling back to full analysis.")
            return self.execute(state)

        changed_files = []
        deleted_files = []

        for line in diff_lines:
            if not line.strip():
                continue
            parts = line.strip().split(maxsplit=1)
            if len(parts) == 2:
                status, rel_path = parts[0], parts[1]
                if status == "D":
                    deleted_files.append(rel_path)
                elif status in ("A", "M") and rel_path.endswith(".py"):
                    changed_files.append(rel_path)

        # 1. Delete stale vector and graph entries for deleted & modified files
        for rel_path in deleted_files + changed_files:
            graph.delete_by_file(repo_id, rel_path)
            vector_store.delete_by_file(repo_id, rel_path)

        # 2. Re-parse and batch index changed/added files
        batch_nodes: List[GraphNode] = []
        batch_rels: List[GraphRelationship] = []
        batch_docs: List[Dict[str, Any]] = []

        for rel_path in changed_files:
            abs_path = os.path.join(state.repository_path, rel_path)
            if os.path.exists(abs_path):
                file_node = GraphNode(id=rel_path, label="File", name=os.path.basename(rel_path), repo_id=repo_id)
                batch_nodes.append(file_node)

                try:
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    if content.strip():
                        batch_docs.append({
                            "id": f"{repo_id}::{rel_path}",
                            "text": content[:2000],
                            "metadata": {"file_path": rel_path, "filename": os.path.basename(rel_path)}
                        })
                except Exception:
                    pass

                self.analyze_python(abs_path, rel_path, repo_id, analysis, batch_nodes, batch_rels, file_node)

        if batch_nodes:
            graph.add_nodes_batch(repo_id, batch_nodes)
        if batch_rels:
            graph.add_relationships_batch(repo_id, batch_rels)
        if batch_docs:
            vector_store.add_documents_batch(repo_id, batch_docs)

        print("\n===== Incremental Codebase Analysis (Git Diff) =====")
        print(f"Repo ID         : {repo_id}")
        print(f"Base Commit     : {base_commit}")
        print(f"Changed Files   : {len(changed_files)}")
        print(f"Deleted Files   : {len(deleted_files)}")
        print(f"Re-indexed Nodes: {len(batch_nodes)}")

        state.codebase_analysis = analysis
        return state

    def analyze_python(self, abs_filename, rel_filename, repo_id, analysis, batch_nodes, batch_rels, file_node):
        try:
            with open(abs_filename, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
        except Exception as e:
            self.logger.warning(f"Unable to parse {abs_filename}: {e}")
            return

        file_imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    file_imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    file_imports.append(node.module)

            elif isinstance(node, ast.ClassDef):
                class_id = f"{rel_filename}::{node.name}"
                class_node = GraphNode(id=class_id, label="Class", name=node.name, repo_id=repo_id)
                batch_nodes.append(class_node)
                batch_rels.append(GraphRelationship(source_id=file_node.id, target_id=class_id, rel_type="CONTAINS", repo_id=repo_id))

                analysis["classes"].append({"name": node.name, "file": rel_filename})

            elif isinstance(node, ast.FunctionDef):
                func_id = f"{rel_filename}::{node.name}"
                func_node = GraphNode(id=func_id, label="Function", name=node.name, repo_id=repo_id)
                batch_nodes.append(func_node)
                batch_rels.append(GraphRelationship(source_id=file_node.id, target_id=func_id, rel_type="CONTAINS", repo_id=repo_id))

                analysis["functions"].append({"name": node.name, "file": rel_filename})

        analysis["imports"].append({"file": rel_filename, "imports": file_imports})
        analysis["dependency_graph"][rel_filename] = file_imports

    def read_requirements(self, filename, analysis):
        for encoding in ["utf-8", "utf-16", "latin-1"]:
            try:
                with open(filename, "r", encoding=encoding) as f:
                    for line in f:
                        dependency = line.strip()
                        if dependency and not dependency.startswith("#"):
                            analysis["dependencies"].append(dependency)
                return
            except UnicodeDecodeError:
                continue
            except Exception as e:
                self.logger.warning(f"Unable to read {filename}: {e}")
                return