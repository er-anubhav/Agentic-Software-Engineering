import unittest
from unittest.mock import MagicMock
from src.domain.models.state import EngineeringState
from src.application.orchestration.dag_compiler import DAGNode, TaskDAG, DAGCompiler
from src.application.agents.planner_agent import PlannerAgent
from src.application.orchestration.execution_planner_agent import ExecutionPlannerAgent


class TestIntelligentPlannerEngine(unittest.TestCase):

    def test_dag_node_15_fields_validation(self):
        node = DAGNode(
            id="repo_layer",
            title="Repository Layer",
            description="Implement ORM repository pattern",
            objective="Decouple persistence from business logic",
            owner_agent="DatabaseAgent",
            priority="CRITICAL",
            estimated_cost=0.08,
            estimated_duration=45.0,
            required_context=["models/db.py"],
            required_tools=["ast_parser"],
            dependencies=["db_migration"],
            outputs=["repo/user_repo.py"],
            validation_strategy="Unit test repository methods",
            rollback_strategy="Revert repository file",
            phase=2
        )

        self.assertEqual(node.id, "repo_layer")
        self.assertEqual(node.owner_agent, "DatabaseAgent")
        self.assertEqual(node.agent, "DatabaseAgent")
        self.assertEqual(node.priority, "CRITICAL")
        self.assertEqual(node.estimated_cost, 0.08)
        self.assertEqual(node.estimated_duration, 45.0)
        self.assertEqual(node.dependencies, ["db_migration"])
        self.assertEqual(node.outputs, ["repo/user_repo.py"])

    def test_dag_compiler_topological_sort_and_parallel_phases(self):
        n1 = DAGNode(id="db_migration", title="DB Migration", owner_agent="DatabaseAgent", dependencies=[])
        n2 = DAGNode(id="repo_layer", title="Repo Layer", owner_agent="DatabaseAgent", dependencies=["db_migration"])
        n3 = DAGNode(id="service_layer", title="Service Layer", owner_agent="CodeGenerationAgent", dependencies=["repo_layer"])
        n4 = DAGNode(id="rest_api", title="REST API", owner_agent="APIAgent", dependencies=["service_layer"])
        n5 = DAGNode(id="integration_tests", title="Integration Tests", owner_agent="TestGenerationAgent", dependencies=["rest_api"])

        compiler = DAGCompiler()
        dag = compiler.compile([n1, n2, n3, n4, n5])

        self.assertFalse(dag.has_cycles())
        sorted_nodes = dag.get_topological_sort()
        self.assertEqual(len(sorted_nodes), 5)
        self.assertEqual(sorted_nodes[0].id, "db_migration")
        self.assertEqual(sorted_nodes[-1].id, "integration_tests")

        parallel_groups = dag.get_parallelizable_groups()
        self.assertGreater(len(parallel_groups), 0)
        self.assertGreater(dag.get_total_estimated_cost(), 0.0)
        self.assertGreater(dag.get_total_estimated_duration(), 0.0)

    def test_planner_agent_execution_with_codebase_analysis(self):
        planner = PlannerAgent()
        planner.invoke_json = MagicMock()
        planner.invoke_json.return_value = {
            "project_category": "feature_development",
            "dag_nodes": [
                {
                    "id": "db_migration",
                    "title": "Database Schema",
                    "description": "Design ORM models",
                    "owner_agent": "DatabaseAgent",
                    "dependencies": []
                },
                {
                    "id": "rest_api",
                    "title": "REST Controller",
                    "description": "Implement FastAPI routes",
                    "owner_agent": "APIAgent",
                    "dependencies": ["db_migration"]
                }
            ]
        }

        state = EngineeringState()
        state.codebase_analysis = {
            "project_type": "brownfield",
            "python_files": ["main.py"],
            "classes": [{"name": "User"}],
            "functions": [{"name": "get_user"}],
            "dependencies": ["fastapi", "pydantic"]
        }

        state = planner.execute(state)
        self.assertEqual(len(state.planner_nodes), 2)
        self.assertEqual(state.planner_nodes[0].id, "db_migration")
        self.assertEqual(state.planner_nodes[1].id, "rest_api")

    def test_execution_planner_agent_phases(self):
        n1 = DAGNode(id="step_db", title="Database", owner_agent="DatabaseAgent", dependencies=[])
        n2 = DAGNode(id="step_api", title="API Routes", owner_agent="APIAgent", dependencies=["step_db"])

        state = EngineeringState()
        state.planner_nodes = [n1, n2]

        exec_planner = ExecutionPlannerAgent()
        state = exec_planner.execute(state)

        plan = state.execution_plan
        self.assertIn("total_estimated_cost_usd", plan)
        self.assertIn("total_estimated_duration_seconds", plan)
        self.assertIn("parallel_execution_phases", plan)
        self.assertEqual(len(plan["execution_plan"]), 2)


if __name__ == "__main__":
    unittest.main()
