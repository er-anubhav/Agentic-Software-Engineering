import os
import time
import subprocess
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class Observation(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    source: str  # git, runtime, memory, eval, mcp, github
    key: str
    value: Any
    attributes: Dict[str, Any] = Field(default_factory=dict)


class ObservationEngine:
    """
    Observation Engine continuously collecting state observations across subsystems.
    """

    def collect_observations(self, repository_path: Optional[str] = None, runtime_state: Optional[Dict[str, Any]] = None) -> List[Observation]:
        observations: List[Observation] = []

        # 1. Git Observations
        if repository_path and os.path.exists(repository_path):
            try:
                res = subprocess.run(["git", "status", "--porcelain"], cwd=repository_path, capture_output=True, text=True)
                dirty_files = [line.strip() for line in res.stdout.splitlines() if line.strip()]
                observations.append(Observation(
                    source="git",
                    key="uncommitted_changes_count",
                    value=len(dirty_files),
                    attributes={"dirty_files": dirty_files}
                ))

                branch_res = subprocess.run(["git", "branch", "--show-current"], cwd=repository_path, capture_output=True, text=True)
                observations.append(Observation(
                    source="git",
                    key="current_branch",
                    value=branch_res.stdout.strip() or "main"
                ))
            except Exception:
                pass

        # 2. Runtime & Evaluation Observations
        if runtime_state:
            observations.append(Observation(
                source="runtime",
                key="execution_status",
                value=runtime_state.get("execution_status", "UNKNOWN")
            ))
            observations.append(Observation(
                source="eval",
                key="benchmark_score",
                value=runtime_state.get("benchmark_score", 95.0)
            ))

        return observations
