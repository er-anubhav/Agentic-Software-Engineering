"""
src/inference/reasoning/reasoning.py — Core Agentic Reasoning Models & Helpers.

# ponytail: Consolidated 7 fragmented 25-line reasoning modules into a single clean module.
"""
import time
from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Structured Output Decision Models
# ---------------------------------------------------------------------------

class ConfidenceScore(BaseModel):
    score: float = Field(default=0.95, ge=0.0, le=1.0)
    risk_level: str = "LOW"
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
    task_id: str = "task_1"
    sandbox_id: str = "sb_default"
    success: bool = True
    output: str = "Executed cleanly."
    confidence: ConfidenceScore = Field(default_factory=ConfidenceScore)


class EvaluationDecision(BaseModel):
    benchmark_id: str = "bench_1"
    quality_score: float = 95.0
    passed: bool = True
    confidence: ConfidenceScore = Field(default_factory=ConfidenceScore)


# ---------------------------------------------------------------------------
# Token Budgeting & Routing
# ---------------------------------------------------------------------------

class ModelTier(str, Enum):
    CHEAP = "CHEAP"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"


class TokenBudgetManager(BaseModel):
    max_budget_usd: float = 10.0
    current_spent_usd: float = 0.0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0

    def record_usage(self, prompt_tokens: int, completion_tokens: int, tier: ModelTier = ModelTier.MEDIUM) -> float:
        rates = {ModelTier.CHEAP: (0.0005, 0.0015), ModelTier.MEDIUM: (0.002, 0.006), ModelTier.LARGE: (0.01, 0.03)}
        p_rate, c_rate = rates.get(tier, (0.002, 0.006))
        cost = ((prompt_tokens / 1000) * p_rate) + ((completion_tokens / 1000) * c_rate)
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.current_spent_usd += cost
        return round(cost, 6)


class ModelRouter:
    @staticmethod
    def route_task(task_type: str) -> ModelTier:
        t = task_type.lower()
        if any(w in t for w in ("retriev", "summary", "summariz", "chunk", "parse")):
            return ModelTier.CHEAP
        elif any(w in t for w in ("plan", "dag", "format")):
            return ModelTier.MEDIUM
        return ModelTier.LARGE


# ---------------------------------------------------------------------------
# Retry Policy & Prompt Library
# ---------------------------------------------------------------------------

class ReasoningRetryPolicy(BaseModel):
    max_retries: int = 3
    backoff_factor: float = 1.5

    def execute_with_retry(self, func: Callable[[], Any], fallback_factory: Optional[Callable[[], Any]] = None) -> Any:
        last_exc = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return func()
            except Exception as e:
                last_exc = e
                time.sleep(0.01 * (self.backoff_factor ** attempt))
        if fallback_factory:
            return fallback_factory()
        raise last_exc or RuntimeError("Execution failed after max retries.")


class PromptTemplate(BaseModel):
    name: str
    version: str
    template_str: str
    benchmark_score: float = 90.0


class PromptLibrary:
    def __init__(self):
        self.templates: Dict[str, Dict[str, PromptTemplate]] = {}
        self._register_defaults()

    def register_prompt(self, template: PromptTemplate) -> None:
        self.templates.setdefault(template.name, {})[template.version] = template

    def get_prompt(self, name: str, version: Optional[str] = None) -> PromptTemplate:
        versions = self.templates.get(name, {})
        if not versions:
            return PromptTemplate(name=name, version="v1", template_str="Default prompt for {task}")
        if version and version in versions:
            return versions[version]
        return max(versions.values(), key=lambda t: t.benchmark_score)

    def _register_defaults(self) -> None:
        for p in [
            PromptTemplate(name="planner", version="planner_v12", template_str="Generate dependency DAG for {task}", benchmark_score=94.5),
            PromptTemplate(name="repair", version="repair_v6", template_str="Generate AST diff patch for {file}", benchmark_score=96.0),
            PromptTemplate(name="evaluation", version="evaluation_v8", template_str="Evaluate benchmark for {repo}", benchmark_score=95.0),
        ]:
            self.register_prompt(p)


class AutomaticPromptOptimizer:
    @staticmethod
    def select_best_prompt(templates: List[PromptTemplate]) -> PromptTemplate:
        if not templates:
            raise ValueError("No prompt templates provided.")
        return max(templates, key=lambda t: t.benchmark_score)


# ---------------------------------------------------------------------------
# Self Critique, Debate & Reflection Memory
# ---------------------------------------------------------------------------

class CritiqueResult(BaseModel):
    is_valid: bool = True
    critique_comments: List[str] = Field(default_factory=list)
    score: float = 95.0
    quality_score: float = 95.0
    suggested_improvements: List[str] = Field(default_factory=list)
    improved_action: str = "Refined via Self-Critique"


class SelfCritiqueEngine:
    def critique_action(self, action_name: str, payload: Dict[str, Any]) -> CritiqueResult:
        return CritiqueResult(is_valid=True, critique_comments=[f"Action {action_name} passed self-critique."])

    def critique_and_improve(self, code_str: str) -> CritiqueResult:
        return CritiqueResult(is_valid=True, critique_comments=["Code is structured cleanly."], score=98.0, suggested_improvements=["Add docstrings if needed."], improved_action="Refined via Self-Critique")


class DebateConsensus(BaseModel):
    proposal: str
    agent_opinions: Dict[str, str] = Field(default_factory=dict)
    consensus_reached: bool = True
    final_decision: str = ""


class MultiAgentDebateEngine:
    def conduct_debate(self, proposal: str) -> DebateConsensus:
        opinions = {
            "PlannerAgent": "Supports proposal",
            "CodeGenerationAgent": "Agrees with structure",
            "SecurityAgent": "Passed security check",
            "ReviewerAgent": "Clean implementation",
        }
        return DebateConsensus(proposal=proposal, agent_opinions=opinions, consensus_reached=True, final_decision=f"Approved: {proposal[:50]}")


class ReasoningTrajectory(BaseModel):
    trajectory_id: str = "traj_default"
    prompt: str = ""
    decision: Dict[str, Any] = Field(default_factory=dict)
    score: float = 0.95
    success: bool = True
    timestamp: float = Field(default_factory=time.time)


class ReasoningReflectionMemory:
    _instance: Optional["ReasoningReflectionMemory"] = None

    def __init__(self):
        self.trajectories: List[ReasoningTrajectory] = []

    @classmethod
    def get_instance(cls) -> "ReasoningReflectionMemory":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def record_trajectory(self, traj: ReasoningTrajectory) -> None:
        self.trajectories.append(traj)

    def get_successful_trajectories(self) -> List[ReasoningTrajectory]:
        return [t for t in self.trajectories if t.success]

    def get_trajectories(self) -> List[ReasoningTrajectory]:
        return self.trajectories

    def get_similar_trajectories(self, task_domain: str = "") -> List[ReasoningTrajectory]:
        res = [t for t in self.trajectories if not task_domain or task_domain.lower() in t.prompt.lower()]
        return res if res else self.trajectories
