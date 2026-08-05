"""
src.domain.events.event_bus — Domain Event Bus & Event Publisher Engine.
"""
import time
import logging
import threading
from typing import Dict, Any, List, Callable, Type
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DomainEvent(BaseModel):
    """Base domain event model."""
    event_id: str
    event_type: str
    timestamp: float = Field(default_factory=time.time)
    payload: Dict[str, Any] = Field(default_factory=dict)


class RepairCompletedEvent(DomainEvent):
    event_type: str = "RepairCompleted"
    target_file: str = ""
    patch_applied: bool = True


class TaskCompletedEvent(DomainEvent):
    event_type: str = "TaskCompleted"
    task_id: str = ""
    agent: str = ""


class WorkflowFailedEvent(DomainEvent):
    event_type: str = "WorkflowFailed"
    workflow_id: str = ""
    error_reason: str = ""


class EventBus:
    """
    Thread-Safe In-Memory Domain Event Bus & Publisher.
    Dispatches domain events to registered handlers (metrics, audit logs, memory).
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._subscribers: Dict[Type[DomainEvent], List[Callable[[DomainEvent], None]]] = {}

    @classmethod
    def get_instance(cls) -> "EventBus":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def subscribe(self, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], None]) -> None:
        """Subscribes an event handler to a domain event type."""
        with self._lock:
            self._subscribers.setdefault(event_type, []).append(handler)
            logger.debug("Registered handler for event '%s'", event_type.__name__)

    def publish(self, event: DomainEvent) -> None:
        """Publishes a domain event to all registered subscribers."""
        event_cls = type(event)
        handlers = []
        with self._lock:
            handlers = list(self._subscribers.get(event_cls, [])) + list(self._subscribers.get(DomainEvent, []))

        logger.info("Publishing domain event '%s' (%s) to %d handlers", event.event_type, event.event_id, len(handlers))
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error("Error in domain event handler for '%s': %s", event.event_type, e, exc_info=True)


def get_event_bus() -> EventBus:
    return EventBus.get_instance()
