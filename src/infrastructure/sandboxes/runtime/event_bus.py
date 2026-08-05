import time
import uuid
from enum import Enum
from typing import Dict, Any, List, Callable, Optional
from pydantic import BaseModel, Field
class EventType(str, Enum):
    JOB_QUEUED = "JobQueued"
    JOB_STARTED = "JobStarted"
    JOB_COMPLETED = "JobCompleted"
    JOB_FAILED = "JobFailed"
    RETRY_STARTED = "RetryStarted"
    RETRY_FINISHED = "RetryFinished"
class Event(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    event_type: EventType
    workflow_id: str
    job_id: str
    timestamp: float = Field(default_factory=time.time)
    data: Dict[str, Any] = Field(default_factory=dict)
class EventBus:
    """
    In-memory Pub/Sub Event Bus for real-time distributed state transitions.
    """
    _instance: Optional["EventBus"] = None
    def __init__(self):
        self.listeners: Dict[EventType, List[Callable[[Event], None]]] = {
            et: [] for et in EventType
        }
        self.event_history: List[Event] = []
    @classmethod
    def get_instance(cls) -> "EventBus":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        self.listeners[event_type].append(callback)
    def publish(self, event: Event) -> None:
        self.event_history.append(event)
        for callback in self.listeners.get(event.event_type, []):
            try:
                callback(event)
            except Exception as e:
                logger.warning("Non-fatal operation exception caught: %s", e)
