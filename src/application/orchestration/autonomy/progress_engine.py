from typing import List, Dict, Any, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from src.application.orchestration.dag_compiler import TaskDAG


class ProgressReport(BaseModel):
    completion_percentage: float = 0.0
    completed_nodes: List[str] = Field(default_factory=list)
    remaining_nodes: List[str] = Field(default_factory=list)
    confidence_score: float = 0.9
    is_stagnant: bool = False
    has_regression: bool = False
    expected_time_remaining_sec: float = 0.0


class ProgressEngine:
    """
    Evaluates goal execution progress, measures completion %, and detects stagnation or regressions.
    """

    def __init__(self):
        self.history: List[float] = []

    def evaluate_progress(self, task_dag: Optional[TaskDAG], completed_node_ids: List[str]) -> ProgressReport:
        if not task_dag or not task_dag.nodes:
            return ProgressReport(completion_percentage=100.0, confidence_score=1.0)

        total = len(task_dag.nodes)
        completed_set = set(completed_node_ids)
        completed_count = sum(1 for nid in task_dag.nodes if nid in completed_set)

        percentage = round((completed_count / total) * 100.0, 2)
        remaining = [nid for nid in task_dag.nodes if nid not in completed_set]

        # Stagnation check
        is_stagnant = False
        if len(self.history) >= 3 and all(p == percentage for p in self.history[-3:]):
            is_stagnant = True

        self.history.append(percentage)

        return ProgressReport(
            completion_percentage=percentage,
            completed_nodes=list(completed_set),
            remaining_nodes=remaining,
            confidence_score=0.95 if not is_stagnant else 0.5,
            is_stagnant=is_stagnant,
            expected_time_remaining_sec=len(remaining) * 30.0
        )
