from enum import Enum
from typing import Dict, Any, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class ModelTier(str, Enum):
    CHEAP = "CHEAP"      # Fast, low-cost (retrieval, summarization)
    MEDIUM = "MEDIUM"    # Medium capability (planning, formatting)
    LARGE = "LARGE"      # High capability (repair, architecture, complex code generation)


class TokenBudgetManager(BaseModel):
    max_budget_usd: float = 10.0
    current_spent_usd: float = 0.0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0

    def record_usage(self, prompt_tokens: int, completion_tokens: int, tier: ModelTier = ModelTier.MEDIUM) -> float:
        cost_rates = {
            ModelTier.CHEAP: (0.0005, 0.0015),
            ModelTier.MEDIUM: (0.002, 0.006),
            ModelTier.LARGE: (0.01, 0.03)
        }
        prompt_rate, comp_rate = cost_rates.get(tier, (0.002, 0.006))
        cost = ((prompt_tokens / 1000) * prompt_rate) + ((completion_tokens / 1000) * comp_rate)

        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.current_spent_usd += cost
        return round(cost, 6)


class ModelRouter:
    """
    Routes tasks dynamically to CHEAP, MEDIUM, or LARGE model tiers based on task domain.
    """

    @staticmethod
    def route_task(task_type: str) -> ModelTier:
        task_lower = task_type.lower()
        if any(kw in task_lower for kw in ("retriev", "summary", "summariz", "chunk", "parse")):
            return ModelTier.CHEAP
        elif any(kw in task_lower for kw in ("plan", "dag", "format")):
            return ModelTier.MEDIUM
        else:
            return ModelTier.LARGE
