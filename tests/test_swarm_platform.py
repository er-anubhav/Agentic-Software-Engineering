import unittest

from src.application.orchestration.swarm.agent_runtime import AgentLifecycleManager, AgentInstance
from src.application.orchestration.swarm.hierarchical_orchestrator import HierarchicalOrchestrator
from src.application.orchestration.swarm.task_marketplace import TaskMarketplace
from src.application.orchestration.swarm.blackboard import SharedBlackboard
from src.application.orchestration.swarm.message_bus import SwarmMessageBus, TypedMessage
from src.application.orchestration.swarm.consensus import SwarmConsensusEngine, ConsensusProposal
from src.application.orchestration.swarm.governance import SwarmGovernanceEngine, GovernancePolicy
from src.application.orchestration.swarm.swarm_optimizer import SwarmOptimizer
from src.application.orchestration.swarm.swarm_engine import FederatedSwarmEngine


class TestSwarmPlatform(unittest.TestCase):

    def setUp(self):
        self.lifecycle_mgr = AgentLifecycleManager()
        self.orchestrator = HierarchicalOrchestrator(self.lifecycle_mgr)
        self.marketplace = TaskMarketplace(self.lifecycle_mgr)
        self.blackboard = SharedBlackboard.get_instance()
        self.message_bus = SwarmMessageBus()
        self.consensus_engine = SwarmConsensusEngine()
        self.governance_engine = SwarmGovernanceEngine()
        self.optimizer = SwarmOptimizer()
        self.swarm_engine = FederatedSwarmEngine.get_instance()

    def test_dynamic_agent_spawning_and_lifecycle(self):
        new_agent = self.lifecycle_mgr.spawn_agent(role="SPECIALIST", capabilities=["security_audit"])
        self.assertEqual(new_agent.status, "IDLE")

        healthy = self.lifecycle_mgr.get_healthy_agents()
        self.assertIn(new_agent, healthy)

        terminated = self.lifecycle_mgr.terminate_agent(new_agent.agent_id)
        self.assertTrue(terminated)
        self.assertNotIn(new_agent, self.lifecycle_mgr.get_healthy_agents())

    def test_hierarchical_orchestration(self):
        plan = self.orchestrator.decompose_and_delegate("Build Microservice")
        self.assertEqual(plan.executive_id, "exec_1")
        self.assertEqual(plan.coordinator_id, "coord_1")
        self.assertGreater(len(plan.assigned_specialists), 0)

    def test_marketplace_bidding(self):
        winning_bid = self.marketplace.post_task("task_code", "code_gen")
        self.assertIsNotNone(winning_bid)
        self.assertEqual(winning_bid.task_id, "task_code")

    def test_blackboard_pub_sub(self):
        received = []
        self.blackboard.subscribe("architecture_design", lambda entry: received.append(entry.value))

        self.blackboard.publish("architecture_design", "Hexagonal Architecture Plan", author_agent_id="exec_1")
        self.assertEqual(self.blackboard.read("architecture_design"), "Hexagonal Architecture Plan")
        self.assertEqual(len(received), 1)

    def test_typed_message_bus_delivery(self):
        msg = TypedMessage(
            msg_id="m1",
            msg_type="PROPOSAL",
            sender_id="coord_1",
            recipient_id="code_agent_1",
            payload={"task": "gen"}
        )
        self.message_bus.send_message(msg)

        inbox = self.message_bus.fetch_messages("code_agent_1")
        self.assertEqual(len(inbox), 1)
        self.assertEqual(inbox[0].msg_id, "m1")

    def test_swarm_consensus_voting(self):
        proposal = ConsensusProposal(
            proposal_id="prop_1",
            decision_type="DEPLOYMENT",
            proposal_text="Deploy to production K8s",
            votes={"a1": True, "a2": True, "a3": False},
            agent_weights={"a1": 1.0, "a2": 1.0, "a3": 0.5}
        )
        evaluated = self.consensus_engine.evaluate_consensus(proposal)
        self.assertTrue(evaluated.is_approved)
        self.assertGreater(evaluated.consensus_score, 0.66)

    def test_governance_enforcement(self):
        self.assertTrue(self.governance_engine.validate_action("exec_1", "Safe code gen"))
        self.assertFalse(self.governance_engine.validate_action("exec_1", "rm_rf_root command"))

        # Emergency kill switch
        self.governance_engine.trigger_emergency_shutdown()
        self.assertFalse(self.governance_engine.validate_action("exec_1", "Safe code gen"))

    def test_swarm_optimizer(self):
        rec = self.optimizer.optimize_team("feature_development")
        self.assertGreater(len(rec.recommended_team), 0)
        self.assertGreater(len(rec.collaboration_graph_edges), 0)

    def test_end_to_end_collaborative_execution(self):
        # Reset governance for clean end-to-end run
        self.swarm_engine.governance_engine.policy.emergency_kill_switch_active = False

        res = self.swarm_engine.execute_swarm_goal("Build REST API microservice")
        self.assertEqual(res.status, "COMPLETED")
        self.assertTrue(res.consensus_approved)
        self.assertTrue(res.governance_passed)


if __name__ == "__main__":
    unittest.main()
