import time
from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field


class PermissionLevel(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    EXECUTE = "EXECUTE"
    ADMIN = "ADMIN"
    SECRETS = "SECRETS"
    INTERNET = "INTERNET"


class MCPTool(BaseModel):
    id: str
    name: str
    version: str = "1.0.0"
    schema_definition: Dict[str, Any] = Field(default_factory=dict)
    permission_level: PermissionLevel = PermissionLevel.READ
    health: str = "HEALTHY"  # HEALTHY, DEGRADED, UNHEALTHY
    timeout_seconds: float = 30.0
    retry_policy: Dict[str, Any] = Field(default_factory=lambda: {"max_retries": 3, "backoff": 1.0})
    attributes: Dict[str, Any] = Field(default_factory=dict)


class MCPToolRegistry:
    """
    Centralized Model Context Protocol (MCP) Tool Registry.
    Registers standard MCP tools (filesystem, git, docker, terminal, postgres, neo4j, redis, qdrant, github, browser, openapi, kubernetes).
    """

    _instance: Optional["MCPToolRegistry"] = None

    def __init__(self):
        self.tools: Dict[str, MCPTool] = {}
        self._register_default_mcp_tools()

    @classmethod
    def get_instance(cls) -> "MCPToolRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_tool(self, tool: MCPTool) -> None:
        self.tools[tool.id] = tool

    def get_tool(self, tool_id: str) -> Optional[MCPTool]:
        return self.tools.get(tool_id)

    def discover_tools(self, min_permission: Optional[PermissionLevel] = None) -> List[MCPTool]:
        if min_permission is None:
            return list(self.tools.values())
        return [t for t in self.tools.values() if t.permission_level == min_permission]

    def _register_default_mcp_tools(self) -> None:
        defaults = [
            MCPTool(id="filesystem", name="Filesystem Tool", permission_level=PermissionLevel.READ),
            MCPTool(id="git", name="Git Version Control Tool", permission_level=PermissionLevel.WRITE),
            MCPTool(id="docker", name="Docker Container Sandbox", permission_level=PermissionLevel.EXECUTE),
            MCPTool(id="terminal", name="Terminal Execution Tool", permission_level=PermissionLevel.EXECUTE),
            MCPTool(id="postgres", name="PostgreSQL Database Tool", permission_level=PermissionLevel.WRITE),
            MCPTool(id="neo4j", name="Neo4j Knowledge Graph Tool", permission_level=PermissionLevel.READ),
            MCPTool(id="redis", name="Redis Key-Value Cache Tool", permission_level=PermissionLevel.READ),
            MCPTool(id="qdrant", name="Qdrant Vector Engine Tool", permission_level=PermissionLevel.READ),
            MCPTool(id="github", name="GitHub API Integration Tool", permission_level=PermissionLevel.INTERNET),
            MCPTool(id="browser", name="Playwright Headless Browser Tool", permission_level=PermissionLevel.INTERNET),
            MCPTool(id="openapi", name="OpenAPI Schema Generator", permission_level=PermissionLevel.READ),
            MCPTool(id="kubernetes", name="Kubernetes Cluster Deployer", permission_level=PermissionLevel.ADMIN)
        ]
        for t in defaults:
            self.register_tool(t)
