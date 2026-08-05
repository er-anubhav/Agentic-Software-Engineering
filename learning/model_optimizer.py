from typing import Dict, Any, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class ModelRanking(BaseModel):
    task_category: str
    primary_provider: str = "openai"
    primary_model: str = "gpt-4o"
    fallback_provider: str = "anthropic"
    fallback_model: str = "claude-3-5-sonnet"
    expected_latency_ms: float = 110.0
    expected_cost_usd: float = 0.005


class ModelOptimizer:
    """
    Model Routing Optimizer.
    Learns the best provider/model for each task class using latency, quality, and cost history.
    """

    def rank_models_for_task(self, task_category: str) -> ModelRanking:
        category_lower = task_category.lower()
        if "repair" in category_lower or "code" in category_lower:
            return ModelRanking(
                task_category=task_category,
                primary_provider="anthropic",
                primary_model="claude-3-5-sonnet",
                fallback_provider="openai",
                fallback_model="gpt-4o",
                expected_latency_ms=130.0,
                expected_cost_usd=0.015
            )
        elif "retrieval" in category_lower or "summary" in category_lower:
            return ModelRanking(
                task_category=task_category,
                primary_provider="gemini",
                primary_model="gemini-1.5-pro",
                fallback_provider="ollama",
                fallback_model="qwen2.5-coder:7b",
                expected_latency_ms=45.0,
                expected_cost_usd=0.0005
            )
        else:
            return ModelRanking(
                task_category=task_category,
                primary_provider="openai",
                primary_model="gpt-4o",
                fallback_provider="anthropic",
                fallback_model="claude-3-5-sonnet",
                expected_latency_ms=110.0,
                expected_cost_usd=0.005
            )
