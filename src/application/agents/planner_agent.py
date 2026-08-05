from typing import List, Dict, Any
from src.application.agents.base_agent import BaseAgent
from src.domain.models.state import EngineeringState
from src.domain.models.dag import DAGNode


class PlannerAgent(BaseAgent):
    """
    Production-grade Autonomous Intelligent Planning Engine (RFC-001).

    Transforms natural language engineering goals and codebase intelligence
    into a dynamic, dependency-aware Engineering DAG.
    """

    def execute(self, state: EngineeringState):
        repo_analysis = getattr(state, "codebase_analysis", {}) or {}
        project_type = repo_analysis.get("project_type", "greenfield")
        python_files = repo_analysis.get("python_files", [])
        existing_classes = repo_analysis.get("classes", [])
        existing_functions = repo_analysis.get("functions", [])
        dependencies = repo_analysis.get("dependencies", [])

        # Format requirements
        requirements_text = "\n".join(
            f"- {req['description'] if isinstance(req, dict) else req.description}"
            for req in state.functional_requirements
        ) if state.functional_requirements else "- Implement user engineering goal."

        prompt = f"""
You are a Staff Software Engineer and AI Systems Architect.

Your job is to transform an engineering goal into an EXECUTABLE DEPENDENCY-AWARE ENGINEERING DAG (Directed Acyclic Graph).

Do NOT generate a simple ordered list. Reason deeply about:
- Repository Mode: {project_type.upper()} ({len(python_files)} python files, {len(existing_classes)} classes, {len(existing_functions)} functions)
- Existing Dependencies: {", ".join(dependencies[:10]) if dependencies else "None"}
- Architectural Constraints, Reusable Code, Database Schemas, REST APIs, Pytest Test Suites, Security Remediation.

For each task node, determine:
- `id`: unique snake_case string (e.g., "db_migration", "repo_layer", "rest_api", "integration_tests")
- `title`: short title
- `description`: technical implementation detail
- `objective`: explicit verification goal
- `owner_agent`: one of ["DatabaseAgent", "APIAgent", "CodeGenerationAgent", "TestGenerationAgent", "ValidationAgent", "SecurityAgent", "RefactoringAgent"]
- `priority`: "CRITICAL", "HIGH", "MEDIUM", or "LOW"
- `estimated_cost`: estimated LLM token cost in USD (e.g. 0.05)
- `estimated_duration`: estimated execution time in seconds (e.g. 30.0)
- `required_context`: list of file paths or AST symbol dependencies
- `required_tools`: list of tools needed (e.g., ["ast_parser", "pytest_runner", "docker_sandbox"])
- `dependencies`: list of prerequisite task `id`s (MUST BE REAL DEPENDENCIES forming a valid DAG)
- `outputs`: expected artifact file paths or code symbols generated
- `validation_strategy`: criteria to verify completion
- `rollback_strategy`: failure recovery plan

Return ONLY valid JSON in the following format:
{{
    "project_category": "feature_development",
    "dag_nodes": [
        {{
            "id": "db_migration",
            "title": "Database Schema & ORM Models",
            "description": "Design database migration scripts and Pydantic/SQLAlchemy ORM models",
            "objective": "Establish persistence layer schema",
            "owner_agent": "DatabaseAgent",
            "priority": "CRITICAL",
            "estimated_cost": 0.05,
            "estimated_duration": 25.0,
            "required_context": ["models/state.py"],
            "required_tools": ["ast_parser"],
            "dependencies": [],
            "outputs": ["models/db.py"],
            "validation_strategy": "Verify ORM table definitions compile",
            "rollback_strategy": "Revert database migration file"
        }},
        {{
            "id": "rest_api",
            "title": "FastAPI REST Controller",
            "description": "Implement HTTP endpoints and request handlers",
            "objective": "Expose REST API endpoints",
            "owner_agent": "APIAgent",
            "priority": "HIGH",
            "estimated_cost": 0.08,
            "estimated_duration": 35.0,
            "required_context": ["models/db.py"],
            "required_tools": ["ast_parser"],
            "dependencies": ["db_migration"],
            "outputs": ["api/routes.py"],
            "validation_strategy": "Verify FastAPI routes register cleanly",
            "rollback_strategy": "Revert API router file"
        }},
        {{
            "id": "pytest_suite",
            "title": "Pytest Unit & Integration Tests",
            "description": "Generate comprehensive unit and integration test suite",
            "objective": "Achieve 100% test pass rate",
            "owner_agent": "TestGenerationAgent",
            "priority": "HIGH",
            "estimated_cost": 0.06,
            "estimated_duration": 30.0,
            "required_context": ["api/routes.py"],
            "required_tools": ["pytest_runner", "docker_sandbox"],
            "dependencies": ["rest_api"],
            "outputs": ["tests/test_routes.py"],
            "validation_strategy": "Run Pytest test suite in isolated container sandbox",
            "rollback_strategy": "Remove generated test file"
        }}
    ]
}}

Functional Requirements:
{requirements_text}
"""

        result = self.invoke_json(prompt)
        raw_nodes = result.get("dag_nodes", [])

        inferred_nodes: List[DAGNode] = []
        for i, node_dict in enumerate(raw_nodes, start=1):
            if isinstance(node_dict, dict):
                node_id = node_dict.get("id") or f"node_{i}"
                dnode = DAGNode(
                    id=node_id,
                    title=node_dict.get("title", f"Task {i}"),
                    description=node_dict.get("description", str(node_dict)),
                    objective=node_dict.get("objective", f"Execute {node_id}"),
                    owner_agent=node_dict.get("owner_agent", "CodeGenerationAgent"),
                    agent=node_dict.get("owner_agent", "CodeGenerationAgent"),
                    priority=node_dict.get("priority", "MEDIUM"),
                    estimated_cost=float(node_dict.get("estimated_cost", 0.05)),
                    estimated_duration=float(node_dict.get("estimated_duration", 30.0)),
                    required_context=node_dict.get("required_context", []),
                    required_tools=node_dict.get("required_tools", []),
                    dependencies=node_dict.get("dependencies", []),
                    outputs=node_dict.get("outputs", []),
                    validation_strategy=node_dict.get("validation_strategy", "Automated Pytest & AST Validation"),
                    rollback_strategy=node_dict.get("rollback_strategy", "Revert workspace changes"),
                    step=i
                )
                inferred_nodes.append(dnode)

        # Fallback if LLM output was empty or invalid
        if not inferred_nodes:
            inferred_nodes = [
                DAGNode(id="db_design", title="Database Design", description="Design persistence layer", owner_agent="DatabaseAgent", step=1),
                DAGNode(id="api_design", title="API Controller Design", description="Implement REST endpoints", owner_agent="APIAgent", dependencies=["db_design"], step=2),
                DAGNode(id="code_impl", title="Core Code Implementation", description="Implement core application logic", owner_agent="CodeGenerationAgent", dependencies=["api_design"], step=3),
                DAGNode(id="test_suite", title="Pytest Suite", description="Generate unit and integration tests", owner_agent="TestGenerationAgent", dependencies=["code_impl"], step=4),
                DAGNode(id="e2e_val", title="Sandbox Validation", description="Verify application in container sandbox", owner_agent="ValidationAgent", dependencies=["test_suite"], step=5)
            ]

        state.planner_nodes = inferred_nodes
        state.tasks = [n.title for n in inferred_nodes]

        print("\n===== Intelligent Planning Engine (RFC-001) =====")
        print(f"Project Category : {result.get('project_category', 'general_engineering')}")
        print(f"Inferred DAG     : {len(inferred_nodes)} dynamic engineering nodes")
        for node in inferred_nodes:
            print(f"  - [{node.priority}] {node.id} ({node.owner_agent}) <- Deps: {node.dependencies}")

        return state