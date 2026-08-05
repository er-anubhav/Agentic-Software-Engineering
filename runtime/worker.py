import uuid
import time
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field

from runtime.job_queue import Job, JobStatus, DurableJobQueue
from runtime.event_bus import EventBus, Event, EventType


class WorkerRole(str, Enum):
    PLANNER = "Planner"
    REPO_INTELLIGENCE = "RepositoryIntelligence"
    RETRIEVER = "Retriever"
    REPAIR = "Repair"
    SANDBOX = "Sandbox"
    EVALUATION = "Evaluation"
    VALIDATION = "Validation"
    CODE_GEN = "CodeGenerationAgent"
    DATABASE = "DatabaseAgent"
    API = "APIAgent"


class Worker(BaseModel):
    worker_id: str = Field(default_factory=lambda: f"wrk_{uuid.uuid4().hex[:8]}")
    role: str = WorkerRole.CODE_GEN
    is_busy: bool = False

    def process_job(self, job: Job, handler_func: Callable[[Job], Dict[str, Any]]) -> Dict[str, Any]:
        self.is_busy = True
        try:
            res = handler_func(job)
            return res
        finally:
            self.is_busy = False


class WorkerPool:
    """
    Configurable autoscaling worker pool manager for parallel distributed agent workloads.
    """

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.workers: List[Worker] = [Worker(role=WorkerRole.CODE_GEN) for _ in range(max_workers)]

    def submit_job(self, job: Job, handler_func: Callable[[Job], Dict[str, Any]]) -> Future:
        worker = next((w for w in self.workers if not w.is_busy), self.workers[0])
        return self.executor.submit(worker.process_job, job, handler_func)

    def shutdown(self) -> None:
        self.executor.shutdown(wait=False)
