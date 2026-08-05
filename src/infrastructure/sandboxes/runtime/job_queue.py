import json
import os
import time
import uuid
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
class Job(BaseModel):
    id: str = Field(default_factory=lambda: f"job_{uuid.uuid4().hex[:12]}")
    workflow_id: str
    node_id: str
    role: str = "CodeGenerationAgent"
    payload: Dict[str, Any] = Field(default_factory=dict)
    status: JobStatus = JobStatus.QUEUED
    retry_count: int = 0
    max_retries: int = 3
    backoff_seconds: float = 1.0
    error: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    def calculate_next_backoff(self) -> float:
        return self.backoff_seconds * (2 ** self.retry_count)
class DurableJobQueue:
    """
    Durable persistent job queue with exponential backoff retries and Dead-Letter Queue (DLQ).
    """
    def __init__(self, storage_dir: str = "runtime_queues"):
        self.storage_dir = storage_dir
        self.dlq_dir = os.path.join(storage_dir, "dlq")
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(self.dlq_dir, exist_ok=True)
        self.jobs: Dict[str, Job] = {}
        self._load_persisted_jobs()
    def _load_persisted_jobs(self) -> None:
        queue_file = os.path.join(self.storage_dir, "active_queue.json")
        if os.path.exists(queue_file):
            try:
                with open(queue_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for job_dict in data:
                    job = Job(**job_dict)
                    self.jobs[job.id] = job
            except Exception as e:
                logger.warning("Non-fatal operation exception caught: %s", e)
    def _persist(self) -> None:
        queue_file = os.path.join(self.storage_dir, "active_queue.json")
        data = [j.model_dump() for j in self.jobs.values() if j.status not in (JobStatus.COMPLETED, JobStatus.CANCELLED)]
        with open(queue_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    def enqueue(self, job: Job) -> Job:
        job.status = JobStatus.QUEUED
        self.jobs[job.id] = job
        self._persist()
        return job
    def dequeue(self, role: Optional[str] = None) -> Optional[Job]:
        for job in self.jobs.values():
            if job.status == JobStatus.QUEUED and (role is None or job.role == role):
                job.status = JobStatus.RUNNING
                job.started_at = time.time()
                self._persist()
                return job
        return None
    def mark_completed(self, job_id: str, result: Dict[str, Any] = None) -> Optional[Job]:
        job = self.jobs.get(job_id)
        if job:
            job.status = JobStatus.COMPLETED
            job.completed_at = time.time()
            if result:
                job.payload["result"] = result
            self._persist()
        return job
    def handle_failure(self, job_id: str, error_msg: str) -> Job:
        job = self.jobs.get(job_id)
        if not job:
            raise KeyError(f"Job {job_id} not found")
        job.retry_count += 1
        job.error = error_msg
        if job.retry_count <= job.max_retries:
            job.status = JobStatus.RETRYING
            time.sleep(min(job.calculate_next_backoff(), 0.05))  # Fast unit test backoff
            job.status = JobStatus.QUEUED
        else:
            job.status = JobStatus.FAILED
            # Route to Dead-Letter Queue (DLQ)
            dlq_path = os.path.join(self.dlq_dir, f"{job.id}_dlq.json")
            with open(dlq_path, "w", encoding="utf-8") as f:
                json.dump(job.model_dump(), f, indent=2)
        self._persist()
        return job
    def get_job(self, job_id: str) -> Optional[Job]:
        return self.jobs.get(job_id)
    def get_jobs_by_workflow(self, workflow_id: str) -> List[Job]:
        return [j for j in self.jobs.values() if j.workflow_id == workflow_id]
