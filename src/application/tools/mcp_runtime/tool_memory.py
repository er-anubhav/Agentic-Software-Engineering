import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ToolChainRecord(BaseModel):
    chain_id: str
    tool_sequence: List[str] = Field(default_factory=list)
    total_duration_ms: float = 0.0
    total_cost_usd: float = 0.0
    success: bool = True
    timestamp: float = Field(default_factory=time.time)


class ToolMemory:
    """
    Stores successful tool chain execution sequences and optimizes tool selection strategy.
    """

    _instance: Optional["ToolMemory"] = None

    def __init__(self):
        self.chain_history: List[ToolChainRecord] = []

    @classmethod
    def get_instance(cls) -> "ToolMemory":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def record_chain(self, tool_sequence: List[str], duration_ms: float, cost_usd: float, success: bool = True) -> ToolChainRecord:
        chain_id = " -> ".join(tool_sequence)
        record = ToolChainRecord(
            chain_id=chain_id,
            tool_sequence=tool_sequence,
            total_duration_ms=round(duration_ms, 2),
            total_cost_usd=round(cost_usd, 4),
            success=success
        )
        self.chain_history.append(record)
        return record

    def get_best_tool_chain(self, target_tools: List[str]) -> List[str]:
        target_set = set(target_tools)
        matching = [c for c in self.chain_history if c.success and target_set.issubset(set(c.tool_sequence))]
        if matching:
            best = min(matching, key=lambda c: c.total_duration_ms)
            return best.tool_sequence
        return target_tools
