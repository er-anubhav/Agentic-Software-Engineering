from agents.requirement_agent import RequirementAgent
from agents.planner_agent import PlannerAgent
from agents.architecture_agent import ArchitectureAgent
from agents.design_agent import DesignAgent
from agents.execution_planner_agent import ExecutionPlannerAgent
from agents.codebase_analysis_agent import CodebaseAnalysisAgent

from agents.database_agent import DatabaseAgent
from agents.api_agent import APIAgent
from agents.validation_agent import ValidationAgent
from agents.code_generation_agent import CodeGenerationAgent
from agents.summary_agent import SummaryAgent

from orchestrator.agent_registry import AgentRegistry
from orchestrator.execution_engine import ExecutionEngine
from agents.human_approval_agent import HumanApprovalAgent
from agents.test_generation_agent import TestGenerationAgent

from models.state import EngineeringState


class Workflow:

    def __init__(self):

        # -----------------------------
        # Core Engineering Agents
        # -----------------------------
        self.requirement_agent = RequirementAgent()
        self.planner_agent = PlannerAgent()
        self.codebase_analysis_agent = CodebaseAnalysisAgent()
        self.architecture_agent = ArchitectureAgent()
        self.design_agent = DesignAgent()
        self.execution_planner_agent = ExecutionPlannerAgent()

        # -----------------------------
        # Execution Engine Registry
        # -----------------------------
        self.registry = AgentRegistry()

        self.registry.register(
            "DatabaseAgent",
            DatabaseAgent()
        )

        self.registry.register(
            "APIAgent",
            APIAgent()
        )

        self.registry.register(
            "ValidationAgent",
            ValidationAgent()
        )
        self.registry.register(
            "HumanApprovalAgent",
            HumanApprovalAgent()
        )

        self.registry.register(
            "CodeGenerationAgent",
            CodeGenerationAgent()
        )
        self.registry.register(
            "TestGenerationAgent",
            TestGenerationAgent()
        )
        self.registry.register(
            "SummaryAgent",
            SummaryAgent()
        )

        self.engine = ExecutionEngine(self.registry)

    def execute(self, requirement: str):

        state = EngineeringState()

        state.requirement = requirement

        # --------------------------------------------------
        # Temporary repository path (Brownfield Demo)
        # --------------------------------------------------
        state.repository_path = r"C:\Projects\agentic-software-engineering"

        print("\n===== Requirement Agent =====")
        state = self.requirement_agent.execute(state)

        print("\n===== Planner Agent =====")
        state = self.planner_agent.execute(state)

        print("\n===== Codebase Analysis Agent =====")
        state = self.codebase_analysis_agent.execute(state)

        print("\n===== Architecture Agent =====")
        state = self.architecture_agent.execute(state)

        print("\n===== Design Agent =====")
        state = self.design_agent.execute(state)

        print("\n===== Execution Planner Agent =====")
        state = self.execution_planner_agent.execute(state)

        state = self.engine.execute(state)

        return state