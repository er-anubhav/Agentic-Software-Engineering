import json
from typing import Dict, Any, List
from observability.tracer import Trace, Span


class TraceExporter:
    """
    Exports trace data to Chrome Trace Event format, Jaeger OTLP format, and standard JSON.
    """

    @staticmethod
    def export_chrome_trace(trace: Trace) -> List[Dict[str, Any]]:
        """
        Exports trace spans to Chrome Trace Event Format (compatible with chrome://tracing / Perfetto).
        """
        chrome_events = []
        for span in trace.spans:
            # Complete event 'X'
            event = {
                "name": span.name,
                "cat": span.subsystem,
                "ph": "X",
                "ts": int(span.start_time * 1000000.0),  # Microseconds
                "dur": int(span.duration_ms * 1000.0),    # Microseconds
                "pid": 1,
                "tid": span.agent,
                "args": {
                    "span_id": span.span_id,
                    "parent_span_id": span.parent_span_id,
                    "status": span.status,
                    "attributes": span.attributes
                }
            }
            chrome_events.append(event)
        return chrome_events

    @staticmethod
    def export_jaeger_otlp(trace: Trace) -> Dict[str, Any]:
        """
        Exports trace spans to Jaeger / OpenTelemetry OTLP JSON format.
        """
        otlp_spans = []
        for span in trace.spans:
            otlp_spans.append({
                "traceId": span.trace_id,
                "spanId": span.span_id,
                "parentSpanId": span.parent_span_id or "",
                "name": span.name,
                "kind": "SPAN_KIND_INTERNAL",
                "startTimeUnixNano": int(span.start_time * 1000000000.0),
                "endTimeUnixNano": int((span.end_time or span.start_time) * 1000000000.0),
                "attributes": [
                    {"key": "agent", "value": {"stringValue": span.agent}},
                    {"key": "subsystem", "value": {"stringValue": span.subsystem}},
                    {"key": "repository", "value": {"stringValue": span.repository}},
                    {"key": "status", "value": {"stringValue": span.status}}
                ],
                "status": {"code": "STATUS_CODE_OK" if span.status == "OK" else "STATUS_CODE_ERROR"}
            })

        return {
            "resourceSpans": [
                {
                    "resource": {
                        "attributes": [
                            {"key": "service.name", "value": {"stringValue": "agentic-se-platform"}}
                        ]
                    },
                    "scopeSpans": [
                        {
                            "spans": otlp_spans
                        }
                    ]
                }
            ]
        }

    @staticmethod
    def export_json(trace: Trace) -> Dict[str, Any]:
        return trace.model_dump()
