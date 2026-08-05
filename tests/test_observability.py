import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient

from src.infrastructure.observability.tracer import Tracer, Trace, Span
from src.infrastructure.observability.metrics import TelemetryCollector, TelemetryMetrics
from src.infrastructure.observability.exporters import TraceExporter
from src.infrastructure.observability.profiler import PerformanceProfiler
from src.infrastructure.observability.regression_detector import RegressionDetector
from src.interfaces.platform.api.app_api import app


class TestObservabilityFramework(unittest.TestCase):

    def setUp(self):
        self.tracer = Tracer.get_instance()
        self.telemetry = TelemetryCollector.get_instance()

    def test_tracer_and_span_context(self):
        run_id = "test_run_101"
        trace = self.tracer.start_trace(run_id=run_id, repository="repo_test")
        span1 = self.tracer.start_span(run_id=run_id, name="plan_dag", agent="PlannerAgent", subsystem="Planning")
        time.sleep(0.01)
        span1.finish(status="OK")

        self.assertEqual(len(trace.spans), 1)
        self.assertEqual(span1.name, "plan_dag")
        self.assertGreater(span1.duration_ms, 0.0)

        log_json = span1.to_structured_log()
        self.assertIn("trace_id", log_json)
        self.assertIn("run_id", log_json)
        self.assertIn("duration_ms", log_json)

    def test_trace_exporters_chrome_and_otlp(self):
        run_id = "test_run_exporter"
        trace = self.tracer.start_trace(run_id=run_id)
        span = self.tracer.start_span(run_id=run_id, name="vector_search", agent="MemoryEngine", subsystem="Retrieval")
        span.finish()

        # Test Chrome Trace format
        chrome_events = TraceExporter.export_chrome_trace(trace)
        self.assertEqual(len(chrome_events), 1)
        self.assertEqual(chrome_events[0]["name"], "vector_search")
        self.assertEqual(chrome_events[0]["ph"], "X")

        # Test Jaeger / OTLP format
        otlp_payload = TraceExporter.export_jaeger_otlp(trace)
        self.assertIn("resourceSpans", otlp_payload)
        spans_list = otlp_payload["resourceSpans"][0]["scopeSpans"][0]["spans"]
        self.assertEqual(len(spans_list), 1)

    def test_performance_profiler_critical_path(self):
        run_id = "test_run_profile"
        trace = self.tracer.start_trace(run_id=run_id)

        s1 = self.tracer.start_span(run_id=run_id, name="fastembed_vectors", agent="VectorMemoryStore", subsystem="Retrieval")
        s1.duration_ms = 120.0
        s1.attributes["prompt_tokens"] = 1200

        s2 = self.tracer.start_span(run_id=run_id, name="sandbox_exec", agent="ValidationAgent", subsystem="Sandbox")
        s2.duration_ms = 450.0
        s2.attributes["retrieval_snippets"] = 15

        profile = PerformanceProfiler.profile_trace(trace)
        self.assertEqual(profile.run_id, run_id)
        self.assertEqual(profile.slowest_subsystem, "Sandbox")
        self.assertEqual(profile.slowest_agent, "ValidationAgent")
        self.assertEqual(profile.largest_prompt_tokens, 1200)
        self.assertEqual(profile.largest_retrieval_snippets, 15)
        self.assertEqual(profile.critical_path[0], "sandbox_exec")

    def test_regression_detector(self):
        baseline = TelemetryMetrics(
            workflow_duration_ms=1000.0,
            tokens_used=1000,
            cost_usd=0.01,
            success_rate=1.0
        )
        current_regressed = TelemetryMetrics(
            workflow_duration_ms=1400.0,  # 40% increase
            tokens_used=1300,              # 30% increase
            cost_usd=0.015,                # 50% increase
            success_rate=0.8               # Drop in quality
        )

        report = RegressionDetector.detect_regressions(current_regressed, baseline, threshold_percent=15.0)
        self.assertTrue(report.has_regression)
        self.assertTrue(report.latency_regression)
        self.assertTrue(report.quality_regression)
        self.assertTrue(report.cost_regression)
        self.assertTrue(report.token_regression)
        self.assertGreater(len(report.regression_warnings), 0)

    def test_observability_api_endpoints(self):
        client = TestClient(app)

        # Health endpoint
        res_health = client.get("/health")
        self.assertEqual(res_health.status_code, 200)

        # Status endpoint
        res_status = client.get("/status")
        self.assertEqual(res_status.status_code, 200)
        self.assertIn("active_worker_threads", res_status.json())

        # Metrics endpoint
        res_metrics = client.get("/metrics")
        self.assertEqual(res_metrics.status_code, 200)
        self.assertIn("overall_success_rate", res_metrics.json())

        # Traces endpoint
        res_traces = client.get("/traces")
        self.assertEqual(res_traces.status_code, 200)
        self.assertIn("total_traces", res_traces.json())

    def test_tracing_concurrent_stress(self):
        def generate_trace_worker(idx: int):
            run_id = f"stress_run_{idx}"
            trace = self.tracer.start_trace(run_id=run_id)
            span = self.tracer.start_span(run_id=run_id, name=f"worker_task_{idx}")
            time.sleep(0.001)
            span.finish()
            return span.duration_ms

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(generate_trace_worker, i) for i in range(50)]
            durations = [f.result() for f in futures]

        self.assertEqual(len(durations), 50)


if __name__ == "__main__":
    unittest.main()
