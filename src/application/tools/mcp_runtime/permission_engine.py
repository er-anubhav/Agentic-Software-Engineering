from typing import List, Set
from src.application.tools.mcp_runtime.tool_registry import PermissionLevel, MCPTool


class PermissionViolationException(Exception):
    pass


class PermissionEngine:
    """
    Fine-Grained Security Permission Engine enforcing READ, WRITE, EXECUTE, ADMIN, SECRETS, INTERNET controls.
    """

    PERMISSION_HIERARCHY = {
        PermissionLevel.READ: 1,
        PermissionLevel.WRITE: 2,
        PermissionLevel.EXECUTE: 3,
        PermissionLevel.INTERNET: 4,
        PermissionLevel.SECRETS: 5,
        PermissionLevel.ADMIN: 6
    }

    @classmethod
    def validate_invocation(cls, granted_permissions: List[PermissionLevel], tool: MCPTool) -> bool:
        granted_set: Set[PermissionLevel] = set(granted_permissions)

        # ADMIN level grants all permissions
        if PermissionLevel.ADMIN in granted_set:
            return True

        required = tool.permission_level
        if required in granted_set:
            return True

        # Check permission hierarchy
        req_val = cls.PERMISSION_HIERARCHY.get(required, 1)
        for g in granted_set:
            if cls.PERMISSION_HIERARCHY.get(g, 1) >= req_val:
                return True

        raise PermissionViolationException(
            f"Access Denied: Agent possesses permissions {[p.value for p in granted_set]}, "
            f"but Tool '{tool.name}' requires permission '{required.value}'."
        )
