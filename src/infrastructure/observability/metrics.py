import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class TelemetryMetrics(BaseModel):
    workflow_duration_ms: float = 0.0
    planner_latency_ms: float = 0.0
    retrieval_latency_ms: float = 0.0
    graph_latency_ms: float = 0.0
    vector_latency_ms: float = 0.0
    sandbox_latency_ms: float = 0.0
    evaluation_latency_ms: float = 0.0
    repair_attempts: int = 0
    tokens_used: int = 0
    cost_usd: float = 0.0
    success_rate: float = 1.0
    patch_size_bytes: int = 0


class TelemetryCollector:
    """
    Centralized Prometheus / OpenTelemetry style metrics collector.
    """

    _instance: Optional["TelemetryCollector"] = None

    def __init__(self):
        self.metrics_history: List[TelemetryMetrics] = []

    @classmethod
    def get_instance(cls) -> "TelemetryCollector":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def record_metrics(self, metrics: TelemetryMetrics) -> None:
        self.metrics_history.append(metrics)

    def get_aggregated_metrics(self) -> Dict[str, Any]:
        if not self.metrics_history:
            return {
                "total_runs": 0,
                "avg_workflow_duration_ms": 0.0,
                "avg_planner_latency_ms": 0.0,
                "avg_retrieval_latency_ms": 0.0,
                "avg_cost_usd": 0.0,
                "overall_success_rate": 1.0
            }

        n = len(self.metrics_history)
        return {
            "total_runs": n,
            "avg_workflow_duration_ms": round(sum(m.workflow_duration_ms for m in self.metrics_history) / n, 2),
            "avg_planner_latency_ms": round(sum(m.planner_latency_ms for m in self.metrics_history) / n, 2),
            "avg_retrieval_latency_ms": round(sum(m.retrieval_latency_ms for m in self.metrics_history) / n, 2),
            "avg_graph_latency_ms": round(sum(m.graph_latency_ms for m in self.metrics_history) / n, 2),
            "avg_vector_latency_ms": round(sum(m.vector_latency_ms for m in self.metrics_history) / n, 2),
            "avg_sandbox_latency_ms": round(sum(m.sandbox_latency_ms for m in self.metrics_history) / n, 2),
            "avg_cost_usd": round(sum(m.cost_usd for m in self.metrics_history) / n, 4),
            "overall_success_rate": round(sum(m.success_rate for m in self.metrics_history) / n, 2)
        }
