from typing import Dict, Any, List
from src.application.tools.mcp_runtime.tool_registry import MCPTool, PermissionLevel, MCPToolRegistry


class GitHubRepositoryTool(MCPTool):
    def __init__(self):
        super().__init__(
            id="github_repository",
            name="GitHub Repository Management Tool",
            permission_level=PermissionLevel.READ
        )


class GitHubIssueTool(MCPTool):
    def __init__(self):
        super().__init__(
            id="github_issue",
            name="GitHub Issue Tracking Tool",
            permission_level=PermissionLevel.WRITE
        )


class GitHubPRTool(MCPTool):
    def __init__(self):
        super().__init__(
            id="github_pr",
            name="GitHub Pull Request Engine Tool",
            permission_level=PermissionLevel.WRITE
        )


class GitHubActionsTool(MCPTool):
    def __init__(self):
        super().__init__(
            id="github_actions",
            name="GitHub Actions Workflow CI/CD Tool",
            permission_level=PermissionLevel.EXECUTE
        )


class GitHubReviewTool(MCPTool):
    def __init__(self):
        super().__init__(
            id="github_review",
            name="GitHub PR Review Feedback Tool",
            permission_level=PermissionLevel.READ
        )


def register_github_mcp_tools():
    registry = MCPToolRegistry.get_instance()
    tools = [
        GitHubRepositoryTool(),
        GitHubIssueTool(),
        GitHubPRTool(),
        GitHubActionsTool(),
        GitHubReviewTool()
    ]
    for t in tools:
        registry.register_tool(t)
