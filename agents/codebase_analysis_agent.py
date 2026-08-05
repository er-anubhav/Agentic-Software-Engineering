import os
import ast

from agents.base_agent import BaseAgent
from models.state import EngineeringState
from memory.graph_db import CodeGraph, GraphNode, GraphRelationship


class CodebaseAnalysisAgent(BaseAgent):

    def execute(self, state: EngineeringState):

        if not state.repository_path or not os.path.exists(state.repository_path):
            state.codebase_analysis = {
                "project_type": "greenfield",
                "message": "No valid repository path supplied."
            }
            return state

        graph = CodeGraph()

        analysis = {
            "project_type": "brownfield",
            "project_structure": [],
            "python_files": [],
            "classes": [],
            "functions": [],
            "imports": [],
            "apis": [],
            "database_models": [],
            "dependencies": [],
            "dependency_graph": {},
            "code_graph": graph
        }

        SKIP_DIRS = {
            ".git", ".idea", ".vscode", "__pycache__", ".pytest_cache",
            ".venv", "venv", "env", "site-packages", "build", "dist", "generated_project"
        }

        for root, dirs, files in os.walk(state.repository_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for file in files:
                path = os.path.join(root, file)
                analysis["project_structure"].append(path)

                if file.endswith(".py"):
                    analysis["python_files"].append(path)
                    file_node = GraphNode(id=path, label="File", name=file)
                    graph.add_node(file_node)
                    self.analyze_python(path, analysis, graph, file_node)

                elif file.lower() == "requirements.txt":
                    self.read_requirements(path, analysis)

        print("\n===== Codebase Analysis =====")
        print(f"Project Type : {analysis['project_type']}")
        print(f"Python Files : {len(analysis['python_files'])}")
        print(f"Classes      : {len(analysis['classes'])}")
        print(f"Functions    : {len(analysis['functions'])}")
        print(f"Dependencies : {len(analysis['dependencies'])}")
        print(f"APIs         : {len(analysis['apis'])}")
        print(f"DB Models    : {len(analysis['database_models'])}")
        print(f"Graph Nodes  : {len(graph.nodes)}")

        state.codebase_analysis = analysis

        return state

    def analyze_python(self, filename, analysis, graph, file_node):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
        except Exception as e:
            self.logger.warning(f"Unable to parse {filename}: {e}")
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
                class_id = f"{filename}::{node.name}"
                class_node = GraphNode(id=class_id, label="Class", name=node.name)
                graph.add_node(class_node)
                graph.add_relationship(GraphRelationship(source_id=file_node.id, target_id=class_id, rel_type="CONTAINS"))

                analysis["classes"].append({
                    "name": node.name,
                    "file": filename
                })

            elif isinstance(node, ast.FunctionDef):
                func_id = f"{filename}::{node.name}"
                func_node = GraphNode(id=func_id, label="Function", name=node.name)
                graph.add_node(func_node)
                graph.add_relationship(GraphRelationship(source_id=file_node.id, target_id=func_id, rel_type="CONTAINS"))

                analysis["functions"].append({
                    "name": node.name,
                    "file": filename
                })

        analysis["imports"].append({
            "file": filename,
            "imports": file_imports
        })
        analysis["dependency_graph"][filename] = file_imports

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