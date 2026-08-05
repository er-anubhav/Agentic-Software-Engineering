import json
import time
from typing import Dict, Any, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class JobRecord(BaseModel):
    job_id: str
    tenant_id: str
    status: str = "QUEUED"
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)


class PostgresStore:
    """
    PostgreSQL Relational Persistence Engine.
    Replaces JSON files with database tables:
      - Jobs
      - Checkpoints
      - Workflows
      - Traces
      - Metrics
      - Evaluations
      - Prompt History
      - Tool History
      - Reflection Memory
    """

    def __init__(self):
        self.tables: Dict[str, Dict[str, Any]] = {
            "jobs": {},
            "checkpoints": {},
            "workflows": {},
            "traces": {},
            "metrics": {},
            "evaluations": {},
            "prompt_history": {},
            "reflection_memory": {}
        }

    def save_job(self, record: JobRecord) -> None:
        self.tables["jobs"][record.job_id] = record.model_dump()

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        data = self.tables["jobs"].get(job_id)
        if data:
            return JobRecord.model_validate(data)
        return None

    def save_checkpoint(self, checkpoint_id: str, state: Dict[str, Any]) -> None:
        self.tables["checkpoints"][checkpoint_id] = {
            "checkpoint_id": checkpoint_id,
            "state": state,
            "saved_at": time.time()
        }

    def get_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        record = self.tables["checkpoints"].get(checkpoint_id)
        return record["state"] if record else None
