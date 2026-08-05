"""
Workflow — Autonomous Engineering Pipeline Coordinator.

Design contract
---------------
- `orchestrator/workflow.py` must NOT import any agent class at the module level.
  Agents are built inside ``_build_registry()`` which runs at ``__init__``
  time inside the Workflow instance, NOT at Python module import time.
- This breaks the ``agents <-> orchestrator`` circular import:
    agents/planner_agent.py         imports orchestrator.dag_compiler
    orchestrator/workflow.py        previously imported agents.planner_agent
  Now ``from src.application.orchestration.workflow import Workflow`` is safe from any module.
"""
import logging
import os
from typing import Optional

from src.application.orchestration.agent_registry import AgentRegistry
from src.application.orchestration.execution_engine import ExecutionEngine
from src.domain.models.state import EngineeringState
from src.core.config import get_settings

logger = logging.getLogger(__name__)


def _build_registry() -> AgentRegistry:
    """
    Build and populate the AgentRegistry with all domain agents.

    All agent imports are intentionally deferred here so that importing
    ``orchestrator.workflow`` does NOT transitively pull in the agent tree
    (which imports from ``orchestrator.dag_compiler``, creating a cycle).
    """
    from src.application.agents.database_agent import DatabaseAgent
    from src.application.agents.api_agent import APIAgent
    from src.application.agents.validation_agent import ValidationAgent
    from src.application.agents.code_generation_agent import CodeGenerationAgent
    from src.application.agents.test_generation_agent import TestGenerationAgent
    from src.application.agents.summary_agent import SummaryAgent
    from src.application.agents.human_approval_agent import HumanApprovalAgent

    registry = AgentRegistry()
    registry.register("DatabaseAgent", DatabaseAgent())
    registry.register("APIAgent", APIAgent())
    registry.register("ValidationAgent", ValidationAgent())
    registry.register("HumanApprovalAgent", HumanApprovalAgent())
    registry.register("CodeGenerationAgent", CodeGenerationAgent())
    registry.register("TestGenerationAgent", TestGenerationAgent())
    registry.register("SummaryAgent", SummaryAgent())
    return registry


class Workflow:
    """
    Autonomous Engineering Pipeline Coordinator.

    Runs the staged agent pipeline:
      RequirementAgent -> PlannerAgent -> CodebaseAnalysisAgent ->
      ArchitectureAgent -> DesignAgent -> ExecutionPlannerAgent ->
      ExecutionEngine (DAG-driven per-step dispatch)
    """

    def __init__(self):
        self.settings = get_settings()

        # Deferred imports — same rationale as _build_registry().
        from src.application.agents.requirement_agent import RequirementAgent
        from src.application.agents.planner_agent import PlannerAgent
        from src.application.agents.architecture_agent import ArchitectureAgent
        from src.application.agents.design_agent import DesignAgent
        from src.application.orchestration.execution_planner_agent import ExecutionPlannerAgent
        from src.application.agents.codebase_analysis_agent import CodebaseAnalysisAgent

        self.requirement_agent = RequirementAgent()
        self.planner_agent = PlannerAgent()
        self.codebase_analysis_agent = CodebaseAnalysisAgent()
        self.architecture_agent = ArchitectureAgent()
        self.design_agent = DesignAgent()
        self.execution_planner_agent = ExecutionPlannerAgent()

        self.registry = _build_registry()
        self.engine = ExecutionEngine(self.registry)

    def execute(self, requirement: str, repository_path: Optional[str] = None) -> EngineeringState:
        """
        Execute the full autonomous engineering pipeline.

        Parameters
        ----------
        requirement:
            Plain-language description of the engineering task.
        repository_path:
            Optional path to an existing repository for brownfield analysis.

        Returns
        -------
        EngineeringState
            Final state after all pipeline stages complete.
        """
        state = EngineeringState()
        state.requirement = requirement

        if repository_path and os.path.exists(repository_path):
            state.repository_path = repository_path
        else:
            state.repository_path = self.settings.repository_path

        logger.info("Pipeline stage: RequirementAgent")
        state = self.requirement_agent.execute(state)

        logger.info("Pipeline stage: PlannerAgent")
        state = self.planner_agent.execute(state)

        logger.info("Pipeline stage: CodebaseAnalysisAgent")
        state = self.codebase_analysis_agent.execute(state)

        logger.info("Pipeline stage: ArchitectureAgent")
        state = self.architecture_agent.execute(state)

        logger.info("Pipeline stage: DesignAgent")
        state = self.design_agent.execute(state)

        logger.info("Pipeline stage: ExecutionPlannerAgent")
        state = self.execution_planner_agent.execute(state)

        logger.info("Pipeline stage: ExecutionEngine (DAG dispatch)")
        state = self.engine.execute(state)

        # Record trajectory experience in ExperienceStore (RFC-013)
        try:
            import uuid
            import time
            from src.application.learning.experience_store import ExperienceStore, EngineeringExperience
            exp_store = ExperienceStore.get_instance()
            exp_store.record_experience(
                EngineeringExperience(
                    experience_id=f"exp_{uuid.uuid4().hex[:8]}",
                    workflow_id=f"wf_{uuid.uuid4().hex[:8]}",
                    task_category="feature_development",
                    trajectory=getattr(state, "tasks", []),
                    success=getattr(state, "execution_status", "COMPLETED") == "COMPLETED",
                    timestamp=time.time()
                )
            )
        except Exception as exc:
            logger.warning(f"Failed to record engineering experience: {exc}")

        return state
