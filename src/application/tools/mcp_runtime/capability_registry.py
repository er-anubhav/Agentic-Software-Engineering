from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from src.application.tools.mcp_runtime.tool_registry import PermissionLevel, MCPToolRegistry
from src.application.tools.mcp_runtime.health_monitor import ToolHealthMonitor


class Capability(BaseModel):
    id: str
    name: str
    description: str = ""
    agent_owner: str = "CodeGenerationAgent"
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    required_permissions: List[PermissionLevel] = Field(default_factory=lambda: [PermissionLevel.READ])
    estimated_cost: float = 0.05
    estimated_latency_ms: float = 250.0
    tool_name: str = "filesystem"
    tool_version: str = "1.0.0"


class CapabilityRegistry:
    """
    Capability Registry binding agent capabilities to standard MCP tools.
    """

    def __init__(self):
        self.capabilities: Dict[str, Capability] = {}
        self._register_default_capabilities()

    def register_capability(self, cap: Capability) -> None:
        self.capabilities[cap.id] = cap

    def get_capability(self, cap_id: str) -> Optional[Capability]:
        return self.capabilities.get(cap_id)

    def _register_default_capabilities(self) -> None:
        caps = [
            Capability(id="cap_db_schema", name="Database Schema Design", agent_owner="DatabaseAgent", tool_name="postgres", required_permissions=[PermissionLevel.WRITE]),
            Capability(id="cap_api_routes", name="REST API Controller", agent_owner="APIAgent", tool_name="openapi", required_permissions=[PermissionLevel.READ]),
            Capability(id="cap_code_gen", name="Core Code Implementation", agent_owner="CodeGenerationAgent", tool_name="filesystem", required_permissions=[PermissionLevel.WRITE]),
            Capability(id="cap_test_gen", name="Pytest Test Suite", agent_owner="TestGenerationAgent", tool_name="terminal", required_permissions=[PermissionLevel.EXECUTE]),
            Capability(id="cap_sandbox_val", name="Container Sandbox Verification", agent_owner="ValidationAgent", tool_name="docker", required_permissions=[PermissionLevel.EXECUTE]),
            Capability(id="cap_security_audit", name="Static Security Vulnerability Scan", agent_owner="SecurityAgent", tool_name="terminal", required_permissions=[PermissionLevel.READ]),
            Capability(id="cap_devops_deploy", name="Kubernetes Manifest Deployment", agent_owner="DevOpsAgent", tool_name="kubernetes", required_permissions=[PermissionLevel.ADMIN])
        ]
        for c in caps:
            self.register_capability(c)


class CapabilityRouter:
    """
    Routes task requirements to owner agents based on capabilities, tool health, and latency.
    """

    def __init__(self, registry: Optional[CapabilityRegistry] = None):
        self.registry = registry or CapabilityRegistry()
        self.health_monitor = ToolHealthMonitor.get_instance()

    def route_task_capability(self, task_objective: str) -> Capability:
        obj_lower = task_objective.lower()

        if "db" in obj_lower or "database" in obj_lower or "schema" in obj_lower:
            cap_id = "cap_db_schema"
        elif "api" in obj_lower or "route" in obj_lower or "endpoint" in obj_lower:
            cap_id = "cap_api_routes"
        elif "test" in obj_lower or "pytest" in obj_lower:
            cap_id = "cap_test_gen"
        elif "validat" in obj_lower or "docker" in obj_lower:
            cap_id = "cap_sandbox_val"
        elif "secur" in obj_lower or "audit" in obj_lower:
            cap_id = "cap_security_audit"
        elif "deploy" in obj_lower or "k8s" in obj_lower:
            cap_id = "cap_devops_deploy"
        else:
            cap_id = "cap_code_gen"

        cap = self.registry.get_capability(cap_id)
        if cap and not self.health_monitor.is_tool_healthy(cap.tool_name):
            # Fallback to general code gen capability if preferred tool is unhealthy
            cap = self.registry.get_capability("cap_code_gen")

        return cap or self.registry.capabilities["cap_code_gen"]
