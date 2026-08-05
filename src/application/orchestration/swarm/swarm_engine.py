from typing import Dict, Any, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

from src.application.orchestration.swarm.agent_runtime import AgentLifecycleManager
from src.application.orchestration.swarm.hierarchical_orchestrator import HierarchicalOrchestrator, DelegationPlan
from src.application.orchestration.swarm.task_marketplace import TaskMarketplace, TaskBid
from src.application.orchestration.swarm.blackboard import SharedBlackboard
from src.application.orchestration.swarm.message_bus import SwarmMessageBus, TypedMessage
from src.application.orchestration.swarm.consensus import SwarmConsensusEngine, ConsensusProposal
from src.application.orchestration.swarm.governance import SwarmGovernanceEngine
from src.application.orchestration.swarm.swarm_optimizer import SwarmOptimizer


class SwarmExecutionResult(BaseModel):
    goal_id: str
    delegation_plan: DelegationPlan
    winning_bids: List[TaskBid] = Field(default_factory=list)
    consensus_approved: bool = True
    governance_passed: bool = True
    status: str = "COMPLETED"


class FederatedSwarmEngine:
    """
    Central Federated Multi-Agent Orchestration & Swarm Intelligence Platform (RFC-014).
    Coordinates:
      Goal -> Executive -> Coordinator -> Marketplace -> Worker Swarm -> Consensus -> Validation -> Learning
    """

    _instance: Optional["FederatedSwarmEngine"] = None

    def __init__(self):
        self.lifecycle_mgr = AgentLifecycleManager()
        self.orchestrator = HierarchicalOrchestrator(self.lifecycle_mgr)
        self.marketplace = TaskMarketplace(self.lifecycle_mgr)
        self.blackboard = SharedBlackboard.get_instance()
        self.message_bus = SwarmMessageBus()
        self.consensus_engine = SwarmConsensusEngine()
        self.governance_engine = SwarmGovernanceEngine()
        self.optimizer = SwarmOptimizer()

    @classmethod
    def get_instance(cls) -> "FederatedSwarmEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def execute_swarm_goal(self, goal_description: str) -> SwarmExecutionResult:
        # Step 1: Governance check
        if not self.governance_engine.validate_action("exec_1", goal_description):
            raise PermissionError("Swarm goal rejected by governance policy.")

        # Step 2: Hierarchical Decomposition
        plan = self.orchestrator.decompose_and_delegate(goal_description)

        # Step 3: Marketplace Bidding for subtasks
        bids = []
        for subtask in plan.task_sub_nodes:
            winning_bid = self.marketplace.post_task(subtask, "code_gen")
            if winning_bid:
                bids.append(winning_bid)

        # Step 4: Publish intermediate proposal to Blackboard
        self.blackboard.publish(
            key=f"proposal_{plan.plan_id}",
            value={"subtasks": plan.task_sub_nodes, "bids": [b.bid_id for b in bids]},
            author_agent_id=plan.executive_id
        )

        # Step 5: Send typed broadcast message
        self.message_bus.send_message(TypedMessage(
            msg_id=f"msg_{plan.plan_id}",
            msg_type="PROPOSAL",
            sender_id=plan.executive_id,
            recipient_id="BROADCAST",
            payload={"plan_id": plan.plan_id}
        ))

        # Step 6: Swarm Consensus Voting
        proposal = ConsensusProposal(
            proposal_id=f"prop_{plan.plan_id}",
            decision_type="ARCHITECTURE",
            proposal_text=goal_description,
            votes={"exec_1": True, "coord_1": True, "code_agent_1": True},
            agent_weights={"exec_1": 2.0, "coord_1": 1.5, "code_agent_1": 1.0}
        )
        evaluated = self.consensus_engine.evaluate_consensus(proposal)

        return SwarmExecutionResult(
            goal_id=f"goal_swarm_1",
            delegation_plan=plan,
            winning_bids=bids,
            consensus_approved=evaluated.is_approved,
            governance_passed=True,
            status="COMPLETED"
        )
