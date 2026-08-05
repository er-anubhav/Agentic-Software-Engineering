import time
from typing import Dict, Any, List, Optional, Callable
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class BlackboardEntry(BaseModel):
    key: str
    value: Any
    author_agent_id: str
    timestamp: float = Field(default_factory=time.time)


class SharedBlackboard:
    """
    Shared Distributed Memory (Blackboard Architecture).
    Stores intermediate reasoning, observations, execution artifacts, design proposals,
    and evaluation reports. Supports publish, subscribe, watch, and conflict resolution.
    """

    _instance: Optional["SharedBlackboard"] = None

    def __init__(self):
        self.data: Dict[str, BlackboardEntry] = {}
        self.subscribers: Dict[str, List[Callable[[BlackboardEntry], None]]] = {}

    @classmethod
    def get_instance(cls) -> "SharedBlackboard":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def publish(self, key: str, value: Any, author_agent_id: str) -> BlackboardEntry:
        entry = BlackboardEntry(key=key, value=value, author_agent_id=author_agent_id)
        self.data[key] = entry

        # Notify subscribers
        for callback in self.subscribers.get(key, []):
            callback(entry)

        return entry

    def read(self, key: str) -> Optional[Any]:
        entry = self.data.get(key)
        return entry.value if entry else None

    def subscribe(self, key: str, callback: Callable[[BlackboardEntry], None]) -> None:
        if key not in self.subscribers:
            self.subscribers[key] = []
        self.subscribers[key].append(callback)
