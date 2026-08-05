from typing import Dict, Any, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class ConsensusProposal(BaseModel):
    proposal_id: str
    decision_type: str  # ARCHITECTURE, REPAIR, DEPLOYMENT
    proposal_text: str
    votes: Dict[str, bool] = Field(default_factory=dict)  # agent_id -> bool
    agent_weights: Dict[str, float] = Field(default_factory=dict)  # agent_id -> float weight
    is_approved: bool = False
    consensus_score: float = 0.0


class SwarmConsensusEngine:
    """
    Swarm Consensus Engine.
    Implements weighted voting and confidence aggregation for architecture, repair,
    and deployment decisions across the agent swarm.
    """

    def evaluate_consensus(self, proposal: ConsensusProposal) -> ConsensusProposal:
        if not proposal.votes:
            proposal.is_approved = False
            return proposal

        total_weight = sum(proposal.agent_weights.get(agent, 1.0) for agent in proposal.votes)
        yes_weight = sum(proposal.agent_weights.get(agent, 1.0) for agent, vote in proposal.votes.items() if vote)

        consensus_score = (yes_weight / total_weight) if total_weight > 0 else 0.0
        proposal.consensus_score = round(consensus_score, 4)
        proposal.is_approved = consensus_score >= 0.66  # 2/3 majority requirement

        return proposal
