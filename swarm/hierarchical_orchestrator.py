from typing import Dict, Any, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

from swarm.agent_runtime import AgentInstance, AgentLifecycleManager


class DelegationPlan(BaseModel):
    plan_id: str
    executive_id: str
    coordinator_id: str
    assigned_specialists: List[str] = Field(default_factory=list)
    task_sub_nodes: List[str] = Field(default_factory=list)
    status: str = "DELEGATED"


class HierarchicalOrchestrator:
    """
    Hierarchical Orchestrator Engine.
    Executes Executive -> Coordinator -> Specialist -> Worker agent delegation and supervision.
    """

    def __init__(self, lifecycle_mgr: Optional[AgentLifecycleManager] = None):
        self.lifecycle_mgr = lifecycle_mgr or AgentLifecycleManager()

    def decompose_and_delegate(self, goal_description: str) -> DelegationPlan:
        agents = self.lifecycle_mgr.get_healthy_agents()
        exec_agent = next((a for a in agents if a.role == "EXECUTIVE"), agents[0])
        coord_agent = next((a for a in agents if a.role == "COORDINATOR"), agents[0])
        specialists = [a.agent_id for a in agents if a.role in ("SPECIALIST", "WORKER")]

        return DelegationPlan(
            plan_id=f"plan_{int(len(agents))}",
            executive_id=exec_agent.agent_id,
            coordinator_id=coord_agent.agent_id,
            assigned_specialists=specialists,
            task_sub_nodes=["subtask_retrieval", "subtask_generation", "subtask_verification"],
            status="DELEGATED"
        )
