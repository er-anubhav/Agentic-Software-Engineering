"""
src.domain.events.outbox — Transactional Event Outbox Engine & Async Dispatcher.
"""
import time
import json
import logging
import asyncio
import threading
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from src.domain.events.event_bus import DomainEvent, get_event_bus

logger = logging.getLogger(__name__)


class OutboxEvent(BaseModel):
    """
    Outbox Event record for transactional persistence prior to dispatch.
    """
    outbox_id: str
    event_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    status: str = "PENDING"
    retry_count: int = 0
    created_at: float = Field(default_factory=time.time)


class OutboxPublisher:
    """
    Thread-safe Outbox Publisher that records events in memory/persistence before dispatch.
    """
    def __init__(self):
        self._outbox_store: Dict[str, OutboxEvent] = {}
        self._lock = threading.Lock()

    def record_event(self, event: DomainEvent) -> OutboxEvent:
        """Stores a domain event into the outbox in PENDING status."""
        outbox_item = OutboxEvent(
            outbox_id=event.event_id,
            event_type=event.event_type,
            payload=event.payload
        )
        with self._lock:
            self._outbox_store[event.event_id] = outbox_item
            logger.info("Recorded event '%s' (%s) into Transactional Outbox", event.event_type, event.event_id)
        return outbox_item

    def get_pending_events(self) -> List[OutboxEvent]:
        with self._lock:
            return [e for e in self._outbox_store.values() if e.status == "PENDING"]

    def mark_dispatched(self, outbox_id: str) -> None:
        with self._lock:
            if outbox_id in self._outbox_store:
                self._outbox_store[outbox_id].status = "DISPATCHED"

    def mark_failed(self, outbox_id: str) -> None:
        with self._lock:
            if outbox_id in self._outbox_store:
                self._outbox_store[outbox_id].status = "FAILED"
                self._outbox_store[outbox_id].retry_count += 1


class OutboxDispatcher:
    """
    Asynchronous Outbox Dispatcher loop processing pending outbox events.
    """
    def __init__(self, publisher: OutboxPublisher):
        self.publisher = publisher
        self.event_bus = get_event_bus()

    async def dispatch_pending(self) -> int:
        """Dispatches all pending outbox events to subscribers asynchronously."""
        pending = self.publisher.get_pending_events()
        dispatched_count = 0
        for item in pending:
            try:
                event = DomainEvent(
                    event_id=item.outbox_id,
                    event_type=item.event_type,
                    payload=item.payload
                )
                self.event_bus.publish(event)
                self.publisher.mark_dispatched(item.outbox_id)
                dispatched_count += 1
            except Exception as e:
                logger.error("Failed outbox event dispatch for '%s': %s", item.outbox_id, e)
                self.publisher.mark_failed(item.outbox_id)
        return dispatched_count
