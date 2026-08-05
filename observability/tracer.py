import json
import logging
import time
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class Span(BaseModel):
    span_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    parent_span_id: Optional[str] = None
    trace_id: str
    run_id: str
    name: str
    agent: str = "System"
    subsystem: str = "Core"
    repository: str = "default"
    planner_version: str = "RFC-001"
    repair_version: str = "RFC-002"
    start_time: float = Field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    status: str = "OK"  # OK, ERROR
    attributes: Dict[str, Any] = Field(default_factory=dict)
    events: List[Dict[str, Any]] = Field(default_factory=list)

    def finish(self, status: str = "OK") -> None:
        self.end_time = time.time()
        self.duration_ms = round((self.end_time - self.start_time) * 1000.0, 2)
        self.status = status

    def to_structured_log(self) -> str:
        return json.dumps({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.start_time)),
            "run_id": self.run_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "agent": self.agent,
            "subsystem": self.subsystem,
            "repository": self.repository,
            "planner_version": self.planner_version,
            "repair_version": self.repair_version,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "attributes": self.attributes
        })


class Trace(BaseModel):
    trace_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:32])
    run_id: str
    repository: str = "default"
    spans: List[Span] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)

    def add_span(self, span: Span) -> None:
        self.spans.append(span)


class Tracer:
    """
    OpenTelemetry-compatible distributed tracing manager.
    """

    _instance: Optional["Tracer"] = None

    def __init__(self):
        self.active_traces: Dict[str, Trace] = {}

    @classmethod
    def get_instance(cls) -> "Tracer":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start_trace(self, run_id: str, repository: str = "default") -> Trace:
        trace = Trace(run_id=run_id, repository=repository)
        self.active_traces[run_id] = trace
        return trace

    def start_span(self, run_id: str, name: str, agent: str = "System", subsystem: str = "Core", parent_span_id: Optional[str] = None) -> Span:
        trace = self.active_traces.get(run_id)
        if not trace:
            trace = self.start_trace(run_id)

        span = Span(
            trace_id=trace.trace_id,
            run_id=run_id,
            name=name,
            agent=agent,
            subsystem=subsystem,
            repository=trace.repository,
            parent_span_id=parent_span_id
        )
        trace.add_span(span)
        return span

    def get_trace(self, run_id: str) -> Optional[Trace]:
        return self.active_traces.get(run_id)
