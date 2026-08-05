"""src.domain.services.relational_store_port — Port for Relational Persistence."""
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class JobRecord(BaseModel):
    job_id: str
    tenant_id: str
    status: str = "QUEUED"
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)


class RelationalStorePort(ABC):
    """Hexagonal Port contract for relational persistence adapters."""

    @abstractmethod
    def save_job(self, record: JobRecord) -> None:
        pass

    @abstractmethod
    def get_job(self, job_id: str) -> Optional[JobRecord]:
        pass

    @abstractmethod
    def save_checkpoint(self, checkpoint_id: str, state: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def get_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        pass
