import json
import os
import subprocess
import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from evaluation.metrics_engine import ExecutionMetrics, PatchComparisonResult
from evaluation.failure_classifier import FailureCategory


class ExperimentRun(BaseModel):
    run_id: str
    git_sha: str
    model: str = "qwen2.5-coder:7b"
    planner_version: str = "RFC-001"
    memory_version: str = "Epic-1-4"
    repair_version: str = "RFC-002"
    status: str = "COMPLETED"
    failure_category: str = FailureCategory.NONE
    task_id: str = "task_01"
    metrics: ExecutionMetrics = Field(default_factory=ExecutionMetrics)
    quality_scores: Dict[str, float] = Field(default_factory=dict)
    patch_results: PatchComparisonResult = Field(default_factory=PatchComparisonResult)
    created_at: float = Field(default_factory=time.time)


class ExperimentTracker:
    """
    Experiment Tracker that logs run_id, git_sha, metrics.json, evaluation.json,
    and maintains an automated Markdown Leaderboard.
    """

    def __init__(self, base_dir: str = "evaluation_runs"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def get_git_sha(self) -> str:
        try:
            res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
            return res.stdout.strip()[:8]
        except Exception:
            return "unknown_sha"

    def log_run(self, run: ExperimentRun) -> str:
        run_dir = os.path.join(self.base_dir, run.run_id)
        os.makedirs(run_dir, exist_ok=True)

        # Save metrics.json
        with open(os.path.join(run_dir, "metrics.json"), "w", encoding="utf-8") as f:
            json.dump(run.metrics.model_dump(), f, indent=2)

        # Save evaluation.json
        eval_payload = {
            "run_id": run.run_id,
            "git_sha": run.git_sha,
            "model": run.model,
            "planner_version": run.planner_version,
            "memory_version": run.memory_version,
            "repair_version": run.repair_version,
            "status": run.status,
            "failure_category": run.failure_category,
            "task_id": run.task_id,
            "quality_scores": run.quality_scores,
            "patch_results": run.patch_results.model_dump(),
            "created_at": run.created_at
        }
        with open(os.path.join(run_dir, "evaluation.json"), "w", encoding="utf-8") as f:
            json.dump(eval_payload, f, indent=2)

        # Update leaderboard.md
        self.update_leaderboard(run)
        return run_dir

    def update_leaderboard(self, run: ExperimentRun) -> None:
        leaderboard_file = os.path.join(self.base_dir, "leaderboard.md")

        header = """# Autonomous Benchmark Leaderboard & Engineering Quality Scorecard

| Run ID | Git SHA | Status | Failure Mode | Overall Score | Repair Score | Diff Accuracy | Duration (s) | Tokens | Cost ($) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""
        row = f"| `{run.run_id[:8]}` | `{run.git_sha}` | **{run.status}** | `{run.failure_category}` | **{run.quality_scores.get('overall_engineering_score', 0.0)}** | {run.quality_scores.get('repair_score', 0.0)} | {run.patch_results.diff_accuracy:.2f} | {run.metrics.total_execution_time_ms / 1000.0:.2f}s | {run.metrics.tokens_used} | ${run.metrics.cost_estimate_usd:.4f} |\n"

        if not os.path.exists(leaderboard_file):
            content = header + row
        else:
            with open(leaderboard_file, "r", encoding="utf-8") as f:
                content = f.read()
            content += row

        with open(leaderboard_file, "w", encoding="utf-8") as f:
            f.write(content)
