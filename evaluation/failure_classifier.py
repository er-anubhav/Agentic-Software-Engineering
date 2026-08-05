import re
from typing import Optional
from sandboxes.base_sandbox import SandboxResult


class FailureCategory:
    NONE = "NONE"
    PLANNING_FAILURE = "PLANNING_FAILURE"
    RETRIEVAL_FAILURE = "RETRIEVAL_FAILURE"
    PATCH_FAILURE = "PATCH_FAILURE"
    COMPILATION_FAILURE = "COMPILATION_FAILURE"
    TEST_FAILURE = "TEST_FAILURE"
    SANDBOX_FAILURE = "SANDBOX_FAILURE"
    TIMEOUT = "TIMEOUT"
    SECURITY_FAILURE = "SECURITY_FAILURE"
    UNKNOWN = "UNKNOWN"


class FailureClassifier:
    """
    Automated taxonomy classifier for workflow failure modes.
    """

    @staticmethod
    def classify_failure(result: Optional[SandboxResult] = None, traceback_str: str = "", status: str = "") -> str:
        if status in ("PASS", "COMPLETED", "PASS_WITH_WARNINGS") and (not result or result.exit_code == 0):
            return FailureCategory.NONE

        if "SandboxUnavailableException" in traceback_str or "Refusing host execution" in traceback_str:
            return FailureCategory.SECURITY_FAILURE

        if result and result.exit_code == 124 or "TimeoutExpired" in traceback_str or "timed out" in traceback_str:
            return FailureCategory.TIMEOUT

        if "SyntaxError" in traceback_str or "IndentationError" in traceback_str or "Compilation" in traceback_str:
            return FailureCategory.COMPILATION_FAILURE

        if "AssertionError" in traceback_str or "FAILED (failures=" in traceback_str or "pytest" in traceback_str.lower():
            return FailureCategory.TEST_FAILURE

        if "Unified diff application error" in traceback_str or "patch application failed" in traceback_str.lower():
            return FailureCategory.PATCH_FAILURE

        if "Docker" in traceback_str or "sandbox" in traceback_str.lower():
            return FailureCategory.SANDBOX_FAILURE

        if "Requirement parsing failed" in traceback_str or "DAG" in traceback_str:
            return FailureCategory.PLANNING_FAILURE

        if "VectorMemoryStore" in traceback_str or "Qdrant" in traceback_str or "Neo4j" in traceback_str:
            return FailureCategory.RETRIEVAL_FAILURE

        return FailureCategory.UNKNOWN
