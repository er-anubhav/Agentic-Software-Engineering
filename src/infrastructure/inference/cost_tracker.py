import time
from typing import Dict, Any, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

from src.infrastructure.inference.provider import LLMResponse


class RequestMetrics(BaseModel):
    trace_id: str = "trace_default"
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    latency_ms: float
    cache_hit: bool
    timestamp: float = Field(default_factory=time.time)


class InferenceCostTracker:
    """
    Per-request token, cost, latency, provider, model, cache hit, and trace ID accounting.
    Integrated into platform Observability.
    """

    def __init__(self):
        self.metrics_history: List[RequestMetrics] = []
        self.total_cost_usd: float = 0.0
        self.total_prompt_tokens: int = 0
        self.total_completion_tokens: int = 0

    def record_request(self, response: LLMResponse, trace_id: str = "trace_default") -> RequestMetrics:
        metrics = RequestMetrics(
            trace_id=trace_id,
            provider=response.provider,
            model=response.model,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            cost_usd=response.cost_usd,
            latency_ms=response.latency_ms,
            cache_hit=response.cache_hit
        )
        self.metrics_history.append(metrics)
        self.total_cost_usd += response.cost_usd
        self.total_prompt_tokens += response.prompt_tokens
        self.total_completion_tokens += response.completion_tokens
        return metrics

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_requests": len(self.metrics_history),
            "total_cost_usd": round(self.total_cost_usd, 6),
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens
        }
