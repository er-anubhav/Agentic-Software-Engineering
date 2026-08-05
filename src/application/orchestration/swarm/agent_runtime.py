import time
from typing import Dict, Any, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class AgentInstance(BaseModel):
    agent_id: str
    role: str = "WORKER"  # EXECUTIVE, COORDINATOR, SPECIALIST, WORKER
    status: str = "IDLE"  # IDLE, RUNNING, SUSPENDED, TERMINATED
    capabilities: List[str] = Field(default_factory=list)
    confidence_score: float = 0.95
    cost_per_task: float = 0.01
    created_at: float = Field(default_factory=time.time)


class AgentLifecycleManager:
    """
    Dynamic Agent Runtime and Lifecycle Manager.
    Handles dynamic spawning, capability registration, agent migration, and health supervision.
    """

    def __init__(self):
        self.agents: Dict[str, AgentInstance] = {}
        self._initialize_default_agents()

    def _initialize_default_agents(self) -> None:
        defaults = [
            AgentInstance(agent_id="exec_1", role="EXECUTIVE", capabilities=["strategy", "decomposition"]),
            AgentInstance(agent_id="coord_1", role="COORDINATOR", capabilities=["scheduling", "supervision"]),
            AgentInstance(agent_id="code_agent_1", role="SPECIALIST", capabilities=["code_gen", "refactoring"]),
            AgentInstance(agent_id="repair_agent_1", role="SPECIALIST", capabilities=["ast_repair", "diff_patch"]),
            AgentInstance(agent_id="qa_agent_1", role="WORKER", capabilities=["testing", "verification"])
        ]
        for a in defaults:
            self.agents[a.agent_id] = a

    def spawn_agent(self, role: str, capabilities: List[str], cost_per_task: float = 0.01) -> AgentInstance:
        agent_id = f"agent_{role.lower()}_{len(self.agents) + 1}"
        agent = AgentInstance(
            agent_id=agent_id,
            role=role,
            status="IDLE",
            capabilities=capabilities,
            cost_per_task=cost_per_task
        )
        self.agents[agent_id] = agent
        return agent

    def terminate_agent(self, agent_id: str) -> bool:
        if agent_id in self.agents:
            self.agents[agent_id].status = "TERMINATED"
            return True
        return False

    def get_healthy_agents(self) -> List[AgentInstance]:
        return [a for a in self.agents.values() if a.status != "TERMINATED"]
