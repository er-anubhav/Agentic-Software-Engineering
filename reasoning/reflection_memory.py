import time
from typing import Dict, Any, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class ReasoningTrajectory(BaseModel):
    trajectory_id: str
    task_type: str
    chosen_tools: List[str] = Field(default_factory=list)
    confidence_score: float = 0.95
    success: bool = True
    reasoning_summary: str = ""
    timestamp: float = Field(default_factory=time.time)


class ReasoningReflectionMemory:
    """
    Stores historical reasoning trajectories, tool choices, confidence scores, and repair successes.
    """

    _instance: Optional["ReasoningReflectionMemory"] = None

    def __init__(self):
        self.trajectories: List[ReasoningTrajectory] = []

    @classmethod
    def get_instance(cls) -> "ReasoningReflectionMemory":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def record_trajectory(self, trajectory: ReasoningTrajectory) -> None:
        self.trajectories.append(trajectory)

    def get_similar_trajectories(self, task_type: str) -> List[ReasoningTrajectory]:
        return [t for t in self.trajectories if t.task_type.lower() in task_type.lower() and t.success]
