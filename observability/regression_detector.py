from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from observability.metrics import TelemetryMetrics


class RegressionReport(BaseModel):
    has_regression: bool = False
    latency_regression: bool = False
    quality_regression: bool = False
    cost_regression: bool = False
    token_regression: bool = False
    latency_delta_percent: float = 0.0
    quality_delta_percent: float = 0.0
    cost_delta_percent: float = 0.0
    token_delta_percent: float = 0.0
    regression_warnings: List[str] = Field(default_factory=list)


class RegressionDetector:
    """
    Compares current workflow run against baseline historical runs to flag regressions.
    """

    @staticmethod
    def detect_regressions(current: TelemetryMetrics, baseline: TelemetryMetrics, threshold_percent: float = 15.0) -> RegressionReport:
        report = RegressionReport()

        # 1. Latency Regression
        if baseline.workflow_duration_ms > 0:
            lat_delta = ((current.workflow_duration_ms - baseline.workflow_duration_ms) / baseline.workflow_duration_ms) * 100.0
            report.latency_delta_percent = round(lat_delta, 2)
            if lat_delta > threshold_percent:
                report.latency_regression = True
                report.has_regression = True
                report.regression_warnings.append(f"Latency increased by {lat_delta:.1f}% (Current: {current.workflow_duration_ms}ms, Baseline: {baseline.workflow_duration_ms}ms)")

        # 2. Quality Regression
        if baseline.success_rate > 0:
            qual_delta = ((current.success_rate - baseline.success_rate) / baseline.success_rate) * 100.0
            report.quality_delta_percent = round(qual_delta, 2)
            if qual_delta < -10.0:
                report.quality_regression = True
                report.has_regression = True
                report.regression_warnings.append(f"Quality dropped by {abs(qual_delta):.1f}%")

        # 3. Cost Regression
        if baseline.cost_usd > 0:
            cost_delta = ((current.cost_usd - baseline.cost_usd) / baseline.cost_usd) * 100.0
            report.cost_delta_percent = round(cost_delta, 2)
            if cost_delta > threshold_percent:
                report.cost_regression = True
                report.has_regression = True
                report.regression_warnings.append(f"Cost increased by {cost_delta:.1f}%")

        # 4. Token Regression
        if baseline.tokens_used > 0:
            tok_delta = ((current.tokens_used - baseline.tokens_used) / baseline.tokens_used) * 100.0
            report.token_delta_percent = round(tok_delta, 2)
            if tok_delta > threshold_percent:
                report.token_regression = True
                report.has_regression = True
                report.regression_warnings.append(f"Token consumption increased by {tok_delta:.1f}%")

        return report
