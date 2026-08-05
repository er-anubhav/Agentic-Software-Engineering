from enum import Enum
from typing import Set, Dict, List, Optional


class Role(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MAINTAINER = "MAINTAINER"
    DEVELOPER = "DEVELOPER"
    REVIEWER = "REVIEWER"
    READ_ONLY = "READ_ONLY"
    SERVICE_ACCOUNT = "SERVICE_ACCOUNT"


class Permission(str, Enum):
    REPO_READ = "REPO_READ"
    REPO_WRITE = "REPO_WRITE"
    WORKSPACE_EXEC = "WORKSPACE_EXEC"
    RUNTIME_ADMIN = "RUNTIME_ADMIN"
    MODEL_ACCESS = "MODEL_ACCESS"
    SECRETS_READ = "SECRETS_READ"
    DEPLOY_ADMIN = "DEPLOY_ADMIN"


ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.OWNER: set(Permission),
    Role.ADMIN: set(Permission),
    Role.MAINTAINER: {
        Permission.REPO_READ,
        Permission.REPO_WRITE,
        Permission.WORKSPACE_EXEC,
        Permission.MODEL_ACCESS,
        Permission.SECRETS_READ
    },
    Role.DEVELOPER: {
        Permission.REPO_READ,
        Permission.REPO_WRITE,
        Permission.WORKSPACE_EXEC,
        Permission.MODEL_ACCESS
    },
    Role.REVIEWER: {
        Permission.REPO_READ,
        Permission.MODEL_ACCESS
    },
    Role.READ_ONLY: {
        Permission.REPO_READ
    },
    Role.SERVICE_ACCOUNT: {
        Permission.REPO_READ,
        Permission.REPO_WRITE,
        Permission.WORKSPACE_EXEC,
        Permission.MODEL_ACCESS
    }
}


class RBACEngine:
    """
    Role-Based Access Control (RBAC) Engine.
    Evaluates permissions across Repositories, Workspaces, Runtime, Models, Secrets, and Deployments.
    """

    @staticmethod
    def has_permission(role_str: str, required_permission: Permission) -> bool:
        try:
            role = Role(role_str.upper())
        except ValueError:
            return False

        allowed = ROLE_PERMISSIONS.get(role, set())
        return required_permission in allowed
