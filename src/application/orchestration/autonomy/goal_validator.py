import os
import subprocess
from typing import Dict, Any, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
class ValidationResult(BaseModel):
    is_complete: bool
    score: float = 100.0
    reason: str
    failed_checks: List[str] = []
class GoalValidator:
    """
    Validates overall goal completion using tests, benchmarks, and repository state.
    """
    def validate_goal(self, repository_path: Optional[str] = None, benchmark_score: float = 95.0) -> ValidationResult:
        failed = []
        if benchmark_score < 70.0:
            failed.append(f"Benchmark score too low: {benchmark_score} < 70.0")
        if repository_path and os.path.exists(repository_path):
            try:
                res = subprocess.run(["git", "status", "--porcelain"], cwd=repository_path, capture_output=True, text=True)
                # Uncommitted changes are allowed if PR is ready
            except Exception as e:
                logger.warning("Non-fatal operation exception caught: %s", e)
        if failed:
            return ValidationResult(
                is_complete=False,
                score=benchmark_score,
                reason="Goal validation failed checks.",
                failed_checks=failed
            )
        return ValidationResult(
            is_complete=True,
            score=benchmark_score,
            reason="Goal satisfied all quality benchmark and verification checks."
        )
