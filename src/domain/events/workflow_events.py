"""src.domain.events.workflow_events — Domain Events for System State Changes."""
import time
from typing import Dict, Any
from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    event_id: str
    event_type: str
    timestamp: float = Field(default_factory=time.time)
    payload: Dict[str, Any] = Field(default_factory=dict)
