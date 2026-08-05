import json
import os
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TrajectoryStep(BaseModel):
    step_index: int
    agent_name: str
    action: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = 0.0
    timestamp: float = Field(default_factory=time.time)


class WorkflowTrajectory(BaseModel):
    run_id: str
    task_id: str
    repository: str
    steps: List[TrajectoryStep] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)


class ReplayEngine:
    """
    Records workflow trajectories to JSON and provides deterministic step-by-step replay.
    """

    def __init__(self, storage_dir: str = "evaluation_runs/trajectories"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def record_step(self, trajectory: WorkflowTrajectory, agent_name: str, action: str, inputs: Dict[str, Any], outputs: Dict[str, Any], duration_ms: float) -> TrajectoryStep:
        step = TrajectoryStep(
            step_index=len(trajectory.steps) + 1,
            agent_name=agent_name,
            action=action,
            inputs=inputs,
            outputs=outputs,
            duration_ms=duration_ms
        )
        trajectory.steps.append(step)
        return step

    def save_trajectory(self, trajectory: WorkflowTrajectory) -> str:
        filepath = os.path.join(self.storage_dir, f"{trajectory.run_id}_trajectory.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(trajectory.model_dump(), f, indent=2)
        return filepath

    def load_trajectory(self, run_id: str) -> Optional[WorkflowTrajectory]:
        filepath = os.path.join(self.storage_dir, f"{run_id}_trajectory.json")
        if not os.path.exists(filepath):
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return WorkflowTrajectory(**data)
