from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ToolHealthStatus(BaseModel):
    tool_id: str
    invocations: int = 0
    failures: int = 0
    timeouts: int = 0
    avg_latency_ms: float = 0.0
    error_rate: float = 0.0
    status: str = "HEALTHY"  # HEALTHY, DEGRADED, UNHEALTHY


class ToolHealthMonitor:
    """
    Tracks tool availability, latency, error rate, timeouts, and health degradation.
    """

    _instance: Optional["ToolHealthMonitor"] = None

    def __init__(self):
        self.health_records: Dict[str, ToolHealthStatus] = {}

    @classmethod
    def get_instance(cls) -> "ToolHealthMonitor":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def record_invocation(self, tool_id: str, duration_ms: float, success: bool, is_timeout: bool = False) -> ToolHealthStatus:
        record = self.health_records.get(tool_id, ToolHealthStatus(tool_id=tool_id))
        record.invocations += 1

        if not success:
            record.failures += 1
        if is_timeout:
            record.timeouts += 1

        # Update average latency
        record.avg_latency_ms = round(
            ((record.avg_latency_ms * (record.invocations - 1)) + duration_ms) / record.invocations,
            2
        )
        record.error_rate = round(record.failures / record.invocations, 2)

        # Health state degradation rules
        if record.error_rate > 0.5 or record.timeouts >= 3:
            record.status = "UNHEALTHY"
        elif record.error_rate > 0.2:
            record.status = "DEGRADED"
        else:
            record.status = "HEALTHY"

        self.health_records[tool_id] = record
        return record

    def is_tool_healthy(self, tool_id: str) -> bool:
        record = self.health_records.get(tool_id)
        if not record:
            return True
        return record.status != "UNHEALTHY"
