import os
import shutil
import unittest
from src.application.orchestration.autonomy.goal_manager import GoalLifecycleManager, GoalStatus, GoalPriority
from src.application.orchestration.autonomy.observation_engine import ObservationEngine
from src.application.orchestration.autonomy.progress_engine import ProgressEngine
from src.application.orchestration.autonomy.replanner import DynamicReplanner
from src.application.orchestration.autonomy.policy_engine import ExecutionPolicyEngine, PolicyAction
from src.application.orchestration.autonomy.goal_validator import GoalValidator
from src.application.orchestration.autonomy.human_gate import HumanApprovalGate
from src.application.orchestration.autonomy.long_horizon_engine import LongHorizonAutonomousEngine
from src.application.orchestration.dag_compiler import DAGCompiler, DAGNode


class TestLongHorizonAutonomousExecution(unittest.TestCase):

    def setUp(self):
        self.goal_mgr = GoalLifecycleManager()
        self.obs_engine = ObservationEngine()
        self.progress_engine = ProgressEngine()
        self.replanner = DynamicReplanner()
        self.policy_engine = ExecutionPolicyEngine()
        self.validator = GoalValidator()
        self.human_gate = HumanApprovalGate()

        self.chk_dir = "/tmp/test_autonomy_checkpoints"
        os.makedirs(self.chk_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.chk_dir):
            shutil.rmtree(self.chk_dir, ignore_errors=True)

    def test_goal_lifecycle_manager_transitions(self):
        goal = self.goal_mgr.create_goal("Build long horizon engine", priority=GoalPriority.HIGH)
        self.assertEqual(goal.status, GoalStatus.CREATED)

        g_updated = self.goal_mgr.transition_status(goal.goal_id, GoalStatus.PLANNING)
        self.assertEqual(g_updated.status, GoalStatus.PLANNING)

        g_exec = self.goal_mgr.transition_status(goal.goal_id, GoalStatus.EXECUTING)
        self.assertEqual(g_exec.status, GoalStatus.EXECUTING)

    def test_observation_engine_collection(self):
        obs = self.obs_engine.collect_observations(runtime_state={"execution_status": "RUNNING", "benchmark_score": 98.0})
        self.assertGreaterEqual(len(obs), 2)
        keys = [o.key for o in obs]
        self.assertIn("execution_status", keys)
        self.assertIn("benchmark_score", keys)

    def test_progress_engine_and_stagnation_detection(self):
        compiler = DAGCompiler()
        n1 = DAGNode(id="n1", title="Task 1", owner_agent="Agent1")
        n2 = DAGNode(id="n2", title="Task 2", owner_agent="Agent2")
        dag = compiler.compile([n1, n2])

        p1 = self.progress_engine.evaluate_progress(dag, ["n1"])
        self.assertEqual(p1.completion_percentage, 50.0)
        self.assertFalse(p1.is_stagnant)

        # Trigger stagnation over 3 identical progress checks
        self.progress_engine.evaluate_progress(dag, ["n1"])
        self.progress_engine.evaluate_progress(dag, ["n1"])
        p_stagnant = self.progress_engine.evaluate_progress(dag, ["n1"])

        self.assertTrue(p_stagnant.is_stagnant)

    def test_dynamic_replanner_dag_mutation(self):
        compiler = DAGCompiler()
        n1 = DAGNode(id="n1", title="Task 1", owner_agent="Agent1")
        n2 = DAGNode(id="n2", title="Task 2", owner_agent="Agent2")
        dag = compiler.compile([n1, n2])

        p = self.progress_engine.evaluate_progress(dag, ["n1"])
        new_dag = self.replanner.replan(dag, ["n1"], [], p)

        self.assertIn("n2", new_dag.nodes)

    def test_policy_engine_actions(self):
        compiler = DAGCompiler()
        n1 = DAGNode(id="n1", title="Task 1", owner_agent="Agent1")
        dag = compiler.compile([n1])
        p = self.progress_engine.evaluate_progress(dag, [])

        dec_cont = self.policy_engine.evaluate_policy(p, failure_count=0)
        self.assertEqual(dec_cont.action, PolicyAction.CONTINUE)

        dec_human = self.policy_engine.evaluate_policy(p, is_high_risk=True)
        self.assertEqual(dec_human.action, PolicyAction.ASK_HUMAN)

        dec_abort = self.policy_engine.evaluate_policy(p, failure_count=5)
        self.assertEqual(dec_abort.action, PolicyAction.ABORT)

    def test_human_approval_gate(self):
        gate_safe = self.human_gate.check_operation("read_file")
        self.assertTrue(gate_safe.approved)

        gate_risk = self.human_gate.check_operation("force_push_main")
        self.assertFalse(gate_risk.approved)

        gate_manual = self.human_gate.approve_operation("force_push_main")
        self.assertTrue(gate_manual.approved)

    def test_goal_validator(self):
        v_pass = self.validator.validate_goal(benchmark_score=95.0)
        self.assertTrue(v_pass.is_complete)

        v_fail = self.validator.validate_goal(benchmark_score=50.0)
        self.assertFalse(v_fail.is_complete)

    def test_long_horizon_autonomous_engine_execution(self):
        engine = LongHorizonAutonomousEngine(storage_dir=self.chk_dir)
        goal = engine.execute_long_horizon_goal("Build continuous replanning engine", max_iterations=3)

        self.assertEqual(goal.status, GoalStatus.COMPLETED)
        self.assertIsNotNone(goal.metadata.get("validation_score"))


if __name__ == "__main__":
    unittest.main()
