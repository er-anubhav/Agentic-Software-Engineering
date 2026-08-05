import uuid
import time
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class GoalStatus(str, Enum):
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    WAITING = "WAITING"
    BLOCKED = "BLOCKED"
    REPLANNING = "REPLANNING"
    VALIDATING = "VALIDATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class GoalPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Goal(BaseModel):
    goal_id: str = Field(default_factory=lambda: f"goal_{uuid.uuid4().hex[:8]}")
    objective: str
    status: GoalStatus = GoalStatus.CREATED
    priority: GoalPriority = GoalPriority.MEDIUM
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    repository_path: Optional[str] = None
    checkpoint_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GoalLifecycleManager:
    """
    Goal Lifecycle Manager managing long-horizon goal states, transitions, and checkpoints.
    """

    def __init__(self):
        self.goals: Dict[str, Goal] = {}

    def create_goal(self, objective: str, repository_path: Optional[str] = None, priority: GoalPriority = GoalPriority.MEDIUM) -> Goal:
        goal = Goal(
            objective=objective,
            repository_path=repository_path,
            priority=priority
        )
        self.goals[goal.goal_id] = goal
        return goal

    def transition_status(self, goal_id: str, new_status: GoalStatus) -> Goal:
        goal = self.goals.get(goal_id)
        if not goal:
            raise KeyError(f"Goal {goal_id} not found.")

        goal.status = new_status
        goal.updated_at = time.time()
        return goal

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        return self.goals.get(goal_id)
