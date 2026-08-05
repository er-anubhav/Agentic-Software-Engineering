import unittest
from mcp_runtime.tool_registry import MCPToolRegistry, MCPTool, PermissionLevel
from mcp_runtime.permission_engine import PermissionEngine, PermissionViolationException
from mcp_runtime.health_monitor import ToolHealthMonitor
from mcp_runtime.capability_registry import CapabilityRegistry, CapabilityRouter, Capability
from mcp_runtime.agent_negotiator import AgentNegotiator
from mcp_runtime.tool_memory import ToolMemory


class TestMCPRuntimeEcosystem(unittest.TestCase):

    def setUp(self):
        self.registry = MCPToolRegistry.get_instance()
        self.health_monitor = ToolHealthMonitor.get_instance()
        self.tool_memory = ToolMemory.get_instance()

    def test_mcp_tool_discovery(self):
        tools = self.registry.discover_tools()
        self.assertGreater(len(tools), 5)
        tool_ids = [t.id for t in tools]
        self.assertIn("filesystem", tool_ids)
        self.assertIn("docker", tool_ids)
        self.assertIn("kubernetes", tool_ids)

    def test_permission_engine_validation(self):
        docker_tool = self.registry.get_tool("docker")
        self.assertIsNotNone(docker_tool)

        # Granted EXECUTE -> Should pass
        valid = PermissionEngine.validate_invocation([PermissionLevel.EXECUTE], docker_tool)
        self.assertTrue(valid)

        # Granted READ only -> Should raise PermissionViolationException
        with self.assertRaises(PermissionViolationException):
            PermissionEngine.validate_invocation([PermissionLevel.READ], docker_tool)

    def test_tool_health_degradation(self):
        # Record 5 consecutive timeouts
        for _ in range(5):
            self.health_monitor.record_invocation("terminal", duration_ms=5000.0, success=False, is_timeout=True)

        is_healthy = self.health_monitor.is_tool_healthy("terminal")
        self.assertFalse(is_healthy)

    def test_capability_router_and_health_fallback(self):
        router = CapabilityRouter()

        # Route database task
        cap_db = router.route_task_capability("Design database models and ORM schema")
        self.assertEqual(cap_db.agent_owner, "DatabaseAgent")

        # Route security audit task
        cap_sec = router.route_task_capability("Perform static security code audit")
        self.assertEqual(cap_sec.agent_owner, "SecurityAgent")

    def test_agent_negotiator_subtask_delegation(self):
        negotiator = AgentNegotiator()
        subtask_req = negotiator.request_subtask_delegation(
            requesting_agent="APIAgent",
            target_agent="DatabaseAgent",
            subtask_description="Generate user table migration"
        )
        self.assertTrue(subtask_req.accepted)
        self.assertIn("DatabaseAgent accepted", subtask_req.response_reason)

    def test_tool_memory_chain_optimization(self):
        self.tool_memory.record_chain(["git", "filesystem", "docker", "terminal"], duration_ms=450.0, cost_usd=0.01)
        self.tool_memory.record_chain(["filesystem", "docker"], duration_ms=200.0, cost_usd=0.005)

        best_chain = self.tool_memory.get_best_tool_chain(["filesystem", "docker"])
        self.assertEqual(best_chain, ["filesystem", "docker"])


if __name__ == "__main__":
    unittest.main()
