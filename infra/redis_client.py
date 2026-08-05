import time
from typing import Dict, Any, List, Optional


class RedisRuntime:
    """
    Redis Runtime for Distributed Job Queues, Distributed Locks, Rate Limiting, Pub/Sub, and Sessions.
    """

    def __init__(self):
        self.queues: Dict[str, List[str]] = {}
        self.locks: Dict[str, float] = {}
        self.pubsub_channels: Dict[str, List[str]] = {}

    def push_queue(self, queue_name: str, payload: str) -> None:
        if queue_name not in self.queues:
            self.queues[queue_name] = []
        self.queues[queue_name].append(payload)

    def pop_queue(self, queue_name: str) -> Optional[str]:
        q = self.queues.get(queue_name, [])
        if q:
            return q.pop(0)
        return None

    def acquire_lock(self, lock_name: str, ttl_seconds: float = 30.0) -> bool:
        now = time.time()
        if lock_name in self.locks:
            if now < self.locks[lock_name]:
                return False  # Lock held
        self.locks[lock_name] = now + ttl_seconds
        return True

    def release_lock(self, lock_name: str) -> None:
        if lock_name in self.locks:
            del self.locks[lock_name]

    def publish(self, channel: str, message: str) -> None:
        if channel not in self.pubsub_channels:
            self.pubsub_channels[channel] = []
        self.pubsub_channels[channel].append(message)
