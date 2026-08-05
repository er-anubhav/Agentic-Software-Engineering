from typing import Dict, Any, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

from swarm.agent_runtime import AgentInstance, AgentLifecycleManager


class TaskBid(BaseModel):
    bid_id: str
    task_id: str
    agent_id: str
    capability_score: float = 0.95
    bid_cost_usd: float = 0.01
    estimated_duration_sec: float = 5.0


class TaskMarketplace:
    """
    Distributed Task Marketplace.
    Agents bid for work based on capability, cost, confidence, and historical performance.
    """

    def __init__(self, lifecycle_mgr: Optional[AgentLifecycleManager] = None):
        self.lifecycle_mgr = lifecycle_mgr or AgentLifecycleManager()
        self.active_bids: Dict[str, List[TaskBid]] = {}

    def post_task(self, task_id: str, required_capability: str) -> Optional[TaskBid]:
        agents = self.lifecycle_mgr.get_healthy_agents()
        bids = []

        for agent in agents:
            if required_capability in agent.capabilities or "strategy" in agent.capabilities:
                bid = TaskBid(
                    bid_id=f"bid_{task_id}_{agent.agent_id}",
                    task_id=task_id,
                    agent_id=agent.agent_id,
                    capability_score=agent.confidence_score,
                    bid_cost_usd=agent.cost_per_task
                )
                bids.append(bid)

        self.active_bids[task_id] = bids

        if not bids:
            return None

        # Award to highest capability_score / lowest cost bid
        winning_bid = max(bids, key=lambda b: (b.capability_score / b.bid_cost_usd))
        return winning_bid
