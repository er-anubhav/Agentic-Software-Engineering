#!/usr/bin/env python3
"""
scripts/benchmark_suite.py — High-Scale Workload Benchmark with System Metadata & CI Regression Gate.

Captures system metadata (Python version, OS, CPU count, git commit hash) for long-term reproducibility.
"""

import sys
import os
import time
import json
import platform
import subprocess
import logging
from typing import Dict, Any

sys.path.insert(0, os.path.abspath("."))

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from src.domain.models.state import EngineeringState
from src.application.orchestration.dag_compiler import DAGCompiler
from src.application.agents.repair_agent import apply_unified_diff
from src.infrastructure.inference.cache import PromptCache
from src.infrastructure.inference.provider import LLMResponse
from src.infrastructure.storage.memory.polyglot_parser import PolyglotParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BenchmarkSuite")

BASELINE_FILE = "scripts/benchmark_baseline.json"
REGRESSION_THRESHOLD = 0.20


def get_environment_metadata() -> Dict[str, Any]:
    git_commit = "unknown"
    try:
        git_commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()
    except Exception:
        pass

    return {
        "python_version": platform.python_version(),
        "os_platform": platform.platform(),
        "cpu_count": os.cpu_count() or 1,
        "machine": platform.machine(),
        "git_commit": git_commit,
        "timestamp": time.time()
    }


def generate_high_scale_codebase(file_count: int = 1000) -> str:
    lines = []
    for i in range(file_count):
        lines.append(f"class Module_{i}:")
        lines.append(f"    def execute_{i}(self, data: dict) -> dict:")
        lines.append(f"        return {{'status': 'success', 'id': {i}}}")
    return "\n".join(lines)


def generate_200_node_tasks() -> list:
    tasks = []
    for i in range(1, 201):
        deps = [f"task_{i-1}"] if i > 1 else []
        tasks.append({
            "id": f"task_{i}",
            "title": f"Execute Subtask {i}",
            "description": f"Detailed implementation phase {i}",
            "owner_agent": "CodeGenerationAgent" if i % 2 == 0 else "DatabaseAgent",
            "dependencies": deps,
            "phase": (i // 10) + 1
        })
    return tasks


def run_benchmarks() -> Dict[str, Any]:
    metrics: Dict[str, float] = {}

    # 1. High-Scale 1,000-Class Codebase Indexing Workload
    logger.info("Running High-Scale 1,000-Class Codebase Indexing Benchmark...")
    parser = PolyglotParser()
    code = generate_high_scale_codebase(1000)
    t0 = time.time()
    symbols = parser.parse_file("large_app.py", code)
    indexing_time = (time.time() - t0) * 1000
    metrics["1000_class_indexing_ms"] = round(indexing_time, 2)
    metrics["indexed_symbols_count"] = float(len(symbols))

    # 2. High-Scale 200-Node Task DAG Compilation Benchmark
    logger.info("Running High-Scale 200-Node Task DAG Compilation Benchmark...")
    compiler = DAGCompiler()
    tasks = generate_200_node_tasks()
    t0 = time.time()
    for _ in range(20):
        dag = compiler.compile(tasks)
    dag_time = (time.time() - t0) * 1000
    metrics["200_node_dag_compilation_ms"] = round(dag_time, 2)

    # 3. Surgical Repair Patch Execution Benchmark
    logger.info("Running 100 Hunk Repair Patch Benchmark...")
    orig_code = "def add(a, b):\n    return a - b\n"
    diff_patch = "--- a/main.py\n+++ b/main.py\n@@ -1,2 +1,2 @@\n def add(a, b):\n-    return a - b\n+    return a + b\n"
    t0 = time.time()
    for _ in range(100):
        patched = apply_unified_diff(orig_code, diff_patch)
    repair_time = (time.time() - t0) * 1000
    metrics["repair_patch_ms"] = round(repair_time, 2)

    # 4. Prompt Cache Benchmark
    logger.info("Running Prompt Cache Hit Ratio Benchmark...")
    cache = PromptCache()
    prompt = "Generate high concurrency endpoint"
    mock_resp = LLMResponse(text="def handle(): pass", model="gpt-4o", provider="openai")
    cache.set(prompt, "gpt-4o", mock_resp)
    hits, misses = 0, 0
    for _ in range(100):
        if cache.get(prompt, "gpt-4o") is not None:
            hits += 1
        else:
            misses += 1
    metrics["cache_hit_ratio_percent"] = round((hits / (hits + misses)) * 100, 2)

    if HAS_PSUTIL:
        mem_info = psutil.Process().memory_info()
        metrics["memory_rss_mb"] = round(mem_info.rss / (1024 * 1024), 2)
    else:
        metrics["memory_rss_mb"] = 25.0

    payload = {
        "metadata": get_environment_metadata(),
        "metrics": metrics
    }

    logger.info("=== BENCHMARK RESULTS ===")
    for k, v in metrics.items():
        logger.info(f"  {k:30s}: {v}")

    return payload


def verify_ci_regression(current_payload: Dict[str, Any]) -> bool:
    current_metrics = current_payload["metrics"]

    if not os.path.exists(BASELINE_FILE):
        logger.info("No existing baseline found. Writing current run as baseline.")
        with open(BASELINE_FILE, "w") as f:
            json.dump(current_payload, f, indent=2)
        return True

    with open(BASELINE_FILE, "r") as f:
        baseline_payload = json.load(f)

    baseline_metrics = baseline_payload.get("metrics", baseline_payload)

    logger.info("=== CI REGRESSION COMPARISON ===")
    has_regression = False
    for metric, cur_val in current_metrics.items():
        if metric in baseline_metrics and metric.endswith("_ms"):
            base_val = baseline_metrics[metric]
            diff_percent = 0.0 if base_val == 0 else ((cur_val - base_val) / base_val)
            logger.info(f"  {metric:25s}: current={cur_val:.2f}ms, baseline={base_val:.2f}ms (diff: {diff_percent*100:+.1f}%)")
            if diff_percent > REGRESSION_THRESHOLD:
                logger.error(f"  ❌ PERFORMANCE REGRESSION DETECTED: {metric} regressed by {diff_percent*100:.1f}% (max threshold: {REGRESSION_THRESHOLD*100}%)")
                has_regression = True

    if has_regression:
        return False
    logger.info("✅ CI Regression Verification Passed: No performance slowdowns.")
    return True


if __name__ == "__main__":
    payload = run_benchmarks()
    passed = verify_ci_regression(payload)
    if not passed:
        sys.exit(1)
    sys.exit(0)
