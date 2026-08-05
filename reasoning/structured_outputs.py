from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ConfidenceScore(BaseModel):
    score: float = Field(default=0.95, ge=0.0, le=1.0)
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH
    missing_context: List[str] = Field(default_factory=list)
    recommended_action: str = "EXECUTE"


class PlanningDecision(BaseModel):
    goal_id: str = "goal_default"
    task_dag_ids: List[str] = Field(default_factory=list)
    priority_ordering: List[str] = Field(default_factory=list)
    selected_tools: List[str] = Field(default_factory=list)
    confidence: ConfidenceScore = Field(default_factory=ConfidenceScore)
    reasoning: str = "Optimal dependency graph planning decision."


class RepairDecision(BaseModel):
    target_file: str = "main.py"
    failing_line: int = 1
    patch_type: str = "unified_diff"
    suggested_patch: str = ""
    confidence: ConfidenceScore = Field(default_factory=ConfidenceScore)
    reasoning: str = "AST surgical patch generated cleanly."


class ExecutionDecision(BaseModel):
    action: str = "CONTINUE"  # CONTINUE, RETRY, ROLLBACK, ASK_HUMAN, ABORT
    target_node_id: Optional[str] = None
    confidence: ConfidenceScore = Field(default_factory=ConfidenceScore)
    reasoning: str = "Execution policy evaluated."


class EvaluationDecision(BaseModel):
    is_passing: bool = True
    overall_score: float = 95.0
    sub_scores: Dict[str, float] = Field(default_factory=lambda: {"planning": 95.0, "repair": 95.0, "execution": 95.0})
    failed_checks: List[str] = Field(default_factory=list)
    confidence: ConfidenceScore = Field(default_factory=ConfidenceScore)
    reasoning: str = "Evaluation suite passed."
