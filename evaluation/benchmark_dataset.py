import json
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class BenchmarkTask(BaseModel):
    """
    Schema for individual SWE-bench / HumanEval inspired benchmark evaluation tasks.
    """
    id: str
    repository: str = "default"
    difficulty: str = "MEDIUM"  # EASY, MEDIUM, HARD
    language: str = "python"
    issue_description: str
    ground_truth_patch: Optional[str] = None
    ground_truth_tests: List[str] = Field(default_factory=list)
    expected_files: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BenchmarkDataset(BaseModel):
    """
    Collection of benchmark tasks for autonomous evaluation runs.
    """
    dataset_name: str = "agentic_se_benchmark_v1"
    tasks: List[BenchmarkTask] = Field(default_factory=list)

    def add_task(self, task: BenchmarkTask) -> None:
        self.tasks.append(task)

    def get_task(self, task_id: str) -> Optional[BenchmarkTask]:
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def save_to_file(self, filepath: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> "BenchmarkDataset":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)
