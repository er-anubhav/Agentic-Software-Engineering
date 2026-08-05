"""
src.infrastructure.observability.tracer — OpenTelemetry & Distributed Trace Context Propagation Engine.
"""
import time
import uuid
import json
import logging
import threading
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TraceSpan(BaseModel):
    span_id: str = Field(default_factory=lambda: f"span_{uuid.uuid4().hex[:8]}")
    trace_id: str = Field(default_factory=lambda: f"trace_{uuid.uuid4().hex[:16]}")
    run_id: str = "run_default"
    parent_span_id: Optional[str] = None
    name: str = "span"
    agent: str = "System"
    subsystem: str = "Core"
    repository: str = "default"
    start_time: float = Field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    attributes: Dict[str, Any] = Field(default_factory=dict)
    status: str = "OK"

    def finish(self, status: str = "OK") -> None:
        self.status = status
        self.end_time = time.time()
        self.duration_ms = round((self.end_time - self.start_time) * 1000, 2)

    def to_structured_log(self) -> str:
        return json.dumps({
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "run_id": self.run_id,
            "name": self.name,
            "agent": self.agent,
            "subsystem": self.subsystem,
            "duration_ms": self.duration_ms,
            "status": self.status
        })


class Trace(BaseModel):
    trace_id: str
    run_id: str = "run_default"
    repository: str = "default"
    created_at: float = Field(default_factory=time.time)
    spans: List[TraceSpan] = Field(default_factory=list)

    def to_chrome_trace_events(self) -> List[Dict[str, Any]]:
        events = []
        for s in self.spans:
            events.append({
                "name": s.name,
                "cat": s.subsystem,
                "ph": "X",
                "ts": int(s.start_time * 1e6),
                "dur": int(s.duration_ms * 1e3),
                "pid": 1,
                "tid": 1,
                "args": s.attributes
            })
        return events

    def to_otlp_spans(self) -> List[Dict[str, Any]]:
        return [{"traceId": self.trace_id, "spanId": s.span_id, "name": s.name} for s in self.spans]


class Tracer:
    """
    OpenTelemetry Tracer with W3C Distributed Trace Context Propagation.
    """
    _instance: Optional["Tracer"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self, trace_id: Optional[str] = None):
        self.trace_id = trace_id or f"trace_{uuid.uuid4().hex[:16]}"
        self.active_spans: Dict[str, TraceSpan] = {}
        self.traces: Dict[str, Trace] = {}

    @property
    def active_traces(self):
        return self.traces

    @classmethod
    def get_instance(cls) -> "Tracer":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        with cls._lock:
            cls._instance = None

    def start_trace(self, run_id: str = "run_default", repository: str = "default") -> Trace:
        t = Trace(trace_id=self.trace_id, run_id=run_id, repository=repository)
        self.traces[run_id] = t
        return t

    def start_span(
        self,
        name: str = "span",
        run_id: str = "run_default",
        agent: str = "System",
        subsystem: str = "Core",
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> TraceSpan:
        span = TraceSpan(
            trace_id=self.trace_id,
            run_id=run_id,
            parent_span_id=parent_span_id,
            name=name,
            agent=agent,
            subsystem=subsystem,
            attributes=attributes or {}
        )
        self.active_spans[span.span_id] = span
        if run_id in self.traces:
            self.traces[run_id].spans.append(span)
        else:
            t = self.start_trace(run_id=run_id)
            t.spans.append(span)
        return span

    def finish_span(self, span_id: str, status: str = "OK") -> Optional[TraceSpan]:
        span = self.active_spans.get(span_id)
        if span:
            span.finish(status=status)
        return span

    def inject_trace_context(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Injects W3C traceparent header into HTTP/RPC dictionary."""
        current_span = list(self.active_spans.values())[-1] if self.active_spans else None
        span_id = current_span.span_id if current_span else "0000000000000000"
        headers["traceparent"] = f"00-{self.trace_id.replace('trace_', '').zfill(32)}-{span_id.replace('span_', '').zfill(16)}-01"
        return headers

    @classmethod
    def extract_trace_context(cls, headers: Dict[str, str]) -> "Tracer":
        """Extracts trace_id from incoming W3C traceparent header."""
        traceparent = headers.get("traceparent", "")
        if traceparent and traceparent.count("-") >= 3:
            parts = traceparent.split("-")
            extracted_trace_id = f"trace_{parts[1][:16]}"
            return cls(trace_id=extracted_trace_id)
        return cls()


Span = TraceSpan
__all__ = ["TraceSpan", "Trace", "Span", "Tracer"]
