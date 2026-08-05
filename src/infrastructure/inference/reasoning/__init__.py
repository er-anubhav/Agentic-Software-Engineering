"""
src/inference/reasoning — Structured LLM Reasoning, Prompt Library & Self-Critique.

# ponytail: Consolidated sub-files into single reasoning.py module.
"""
from src.infrastructure.inference.reasoning.reasoning import (
    ConfidenceScore,
    PlanningDecision,
    RepairDecision,
    ExecutionDecision,
    EvaluationDecision,
    ModelTier,
    TokenBudgetManager,
    ModelRouter,
    ReasoningRetryPolicy,
    PromptTemplate,
    PromptLibrary,
    AutomaticPromptOptimizer,
    CritiqueResult,
    SelfCritiqueEngine,
    DebateConsensus,
    MultiAgentDebateEngine,
    ReasoningTrajectory,
    ReasoningReflectionMemory,
)
from src.infrastructure.inference.reasoning.reasoning_engine import UnifiedReasoningEngine

__all__ = [
    "ConfidenceScore",
    "PlanningDecision",
    "RepairDecision",
    "ExecutionDecision",
    "EvaluationDecision",
    "ModelTier",
    "TokenBudgetManager",
    "ModelRouter",
    "ReasoningRetryPolicy",
    "PromptTemplate",
    "PromptLibrary",
    "AutomaticPromptOptimizer",
    "CritiqueResult",
    "SelfCritiqueEngine",
    "DebateConsensus",
    "MultiAgentDebateEngine",
    "ReasoningTrajectory",
    "ReasoningReflectionMemory",
    "UnifiedReasoningEngine",
]
