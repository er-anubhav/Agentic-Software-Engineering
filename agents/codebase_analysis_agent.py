import os
import ast

from models.state import EngineeringState


class CodebaseAnalysisAgent:

    def execute(self, state: EngineeringState):

        # ----------------------------
        # Greenfield Check
        # ----------------------------
        if not state.repository_path:

            state.codebase_analysis = {
                "project_type": "greenfield",
                "message": "No repository supplied."
            }

            return state

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
            "dependency_graph": {}
        }

        SKIP_DIRS = {
            ".git",
            ".idea",
            ".vscode",
            "__pycache__",
            ".pytest_cache",
            ".venv",
            "venv",
            "env",
            "site-packages",
            "build",
            "dist",
            "generated_project"
        }

        # ----------------------------
        # Repository Scan
        # ----------------------------
        for root, dirs, files in os.walk(state.repository_path):

            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for file in files:

                path = os.path.join(root, file)

                analysis["project_structure"].append(path)

                if file.endswith(".py"):

                    analysis["python_files"].append(path)
                    self.analyze_python(path, analysis)

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

        state.codebase_analysis = analysis

        return state

    def analyze_python(self, filename, analysis):

        try:

            with open(filename, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

        except Exception as e:

            print(f"Unable to parse {filename}: {e}")
            return

        file_imports = []

        for node in ast.walk(tree):

            # -----------------------------
            # Imports
            # -----------------------------
            if isinstance(node, ast.Import):

                for alias in node.names:
                    file_imports.append(alias.name)

            elif isinstance(node, ast.ImportFrom):

                if node.module:
                    file_imports.append(node.module)

            # -----------------------------
            # Classes
            # -----------------------------
            elif isinstance(node, ast.ClassDef):

                analysis["classes"].append({
                    "name": node.name,
                    "file": filename
                })

                is_model = False

                # Detect inheritance
                for base in node.bases:

                    if isinstance(base, ast.Name):

                        if base.id.lower() in (
                            "base",
                            "model",
                            "declarativebase"
                        ):
                            is_model = True

                    elif isinstance(base, ast.Attribute):

                        if base.attr.lower() in (
                            "base",
                            "model",
                            "declarativebase"
                        ):
                            is_model = True

                # Detect __tablename__ or ORM columns
                for stmt in node.body:

                    if isinstance(stmt, ast.Assign):

                        # __tablename__
                        for target in stmt.targets:

                            if (
                                isinstance(target, ast.Name)
                                and target.id == "__tablename__"
                            ):
                                is_model = True

                        # Column()
                        if isinstance(stmt.value, ast.Call):

                            if isinstance(stmt.value.func, ast.Name):

                                if stmt.value.func.id in (
                                    "Column",
                                    "mapped_column"
                                ):
                                    is_model = True

                if is_model:

                    analysis["database_models"].append({
                        "name": node.name,
                        "file": filename
                    })

            # -----------------------------
            # Functions
            # -----------------------------
            elif isinstance(node, ast.FunctionDef):

                analysis["functions"].append({
                    "name": node.name,
                    "file": filename
                })

                for decorator in node.decorator_list:

                    if not isinstance(decorator, ast.Call):
                        continue

                    func = decorator.func

                    if not isinstance(func, ast.Attribute):
                        continue

                    method = func.attr.lower()

                    if method not in (
                        "get",
                        "post",
                        "put",
                        "delete",
                        "patch",
                        "options",
                        "head"
                    ):
                        continue

                    route = "/"

                    if decorator.args:

                        arg = decorator.args[0]

                        if isinstance(arg, ast.Constant):
                            route = arg.value

                        elif isinstance(arg, ast.Str):
                            route = arg.s

                    router_name = ""

                    if isinstance(func.value, ast.Name):
                        router_name = func.value.id

                    analysis["apis"].append({
                        "router": router_name,
                        "method": method.upper(),
                        "path": route,
                        "function": node.name,
                        "file": filename
                    })

        analysis["imports"].append({
            "file": filename,
            "imports": file_imports
        })

        analysis["dependency_graph"][filename] = file_imports

    def read_requirements(self, filename, analysis):

        encodings = [
            "utf-8",
            "utf-16",
            "latin-1"
        ]

        for encoding in encodings:

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

                print(f"Unable to read {filename}: {e}")
                return